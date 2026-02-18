import asyncio

import aiohttp
from playwright.async_api import Page

from tikorgzo.console import console
from tikorgzo.core.extractors.base import BaseExtractor
from tikorgzo.core.extractors.tikwm.browser import ScrapeBrowser
from tikorgzo.core.extractors.tikwm.constants import ELEMENT_LOAD_TIMEOUT, TIKTOK_DOWNLOADER_URL, WEBPAGE_LOAD_TIMEOUT
from tikorgzo.core.video import helpers as fn
from tikorgzo.core.video.model import Video
from tikorgzo.exceptions import ExtractionTimeoutError, HrefLinkMissingError, HtmlElementMissingError, MissingPlaywrightBrowserError, URLParsingError, VagueErrorMessageError


class TikWMExtractor(BaseExtractor):
    """A link extractor from TikWM API."""

    def __init__(self, extraction_delay: float) -> None:
        self.browser: ScrapeBrowser | None = None
        super().__init__(extraction_delay)

    async def process_video_links(self, videos: list[Video]) -> list[Video | BaseException]:
        tasks = [self._extract(video) for video in videos]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def cleanup(self) -> None:
        if self.browser:
            await self.browser.cleanup()

    async def initialize(self) -> None:
        try:
            self.browser = ScrapeBrowser()
            await self.browser.initialize()
        except Exception:
            if self.browser:
                await self.browser.cleanup()
            raise

    async def _extract(self, video: Video) -> Video:
        # The code is wrapped inside the semaphore so that a maximum number of tasks will be handled
        # at a time
        async with self.semaphore:
            try:
                if self.browser is None or self.browser.context is None:
                    raise MissingPlaywrightBrowserError  # noqa: TRY301

                page = await self.browser.context.new_page()
                await self._open_webpage(page)
                await self._submit_link(page, video.video_link)
                video = await self._get_download_link(page, video)
                await page.close()

                return video
            except (
                ExtractionTimeoutError,
                HrefLinkMissingError,
                HtmlElementMissingError,
                URLParsingError,
                VagueErrorMessageError,
            ) as e:
                console.print(f"Skipping {video.video_id} due to: [red]{type(e).__name__}: {e}[/red]")
                # Needs to re-raise so that the mainline script (main.py) will caught this exception
                # thus, the program can filter tasks that are successful and not these failed tasks
                # due to these exception
                raise e  # noqa: TRY201
            except asyncio.CancelledError as e:
                console.print(f"Skipping {video.video_id} due to: [red]UserCancelledAction[/red]")
                # Needs to re-raise so that the mainline script (main.py) will caught this exception
                # thus, the program can filter tasks that are successful and not these failed tasks
                # due to these exception
                raise e  # noqa: TRY201
            except Exception as e:
                console.print(f"Skipping {video.video_id} due to: [red]{type(e).__name__}: {e}[/red]")
                raise e  # noqa: TRY201

    async def _open_webpage(self, page: Page) -> None:
        try:
            await page.goto(TIKTOK_DOWNLOADER_URL, timeout=WEBPAGE_LOAD_TIMEOUT)
            await page.wait_for_load_state("networkidle", timeout=WEBPAGE_LOAD_TIMEOUT)
        except Exception:
            msg = "Cannot load webpage due to timeout; the website may be slow."
            raise ExtractionTimeoutError(msg) from None

    async def _submit_link(self, page: Page, video_link: str) -> None:
        input_field_selector = "input#params"

        try:
            await page.locator(input_field_selector).fill(video_link, timeout=ELEMENT_LOAD_TIMEOUT)
        except Exception:
            raise HtmlElementMissingError(input_field_selector) from None

        submit_button_selector = "button:has-text('Submit')"

        while True:
            try:
                await page.locator(submit_button_selector).click()
            except Exception:
                raise HtmlElementMissingError(submit_button_selector) from None

            # Wait for either the limit message or the next step to appear
            limit_selector = "div:has-text('Free Api Limit: 1 request/second.')"
            try:
                # Wait briefly to see if the limit message appears
                await page.wait_for_selector(limit_selector, state="visible", timeout=2000)
                # If limit message appears, wait and retry
                await asyncio.sleep(self._extraction_delay)
                continue
            except Exception:
                # If limit message does not appear, break loop
                break

    async def _get_download_link(self, page: Page, video: Video) -> Video:
        download_link_selector = "a:has-text('Watermark')"
        parsing_error_selector = "div:has-text('Url parsing is failed!')"
        vague_error_selector = "div:has-text('error')"

        await page.wait_for_selector(f"{download_link_selector}, {parsing_error_selector}, {vague_error_selector}", state="visible", timeout=ELEMENT_LOAD_TIMEOUT)

        if await page.query_selector(parsing_error_selector):
            raise URLParsingError
        if await page.query_selector(vague_error_selector):
            # The API sometimes shows "error" message banner when trying to get the download link.
            # However, it doesn't tell anything about what is the error, hence the reason
            # why exceptiuon is named like this
            raise VagueErrorMessageError

        download_element = await page.query_selector(download_link_selector)

        if download_element is None:
            raise HtmlElementMissingError(download_link_selector)

        download_url = await download_element.get_attribute("href")

        if not download_url:
            raise HrefLinkMissingError

        # Username is scraped here in case that the Video instance doesn't have a username
        # yet. This is important so that the videos are grouped by username when downloaded.
        h4_elements = page.locator("h4")
        username = await h4_elements.nth(2).inner_text()

        if video.username is None:
            video.username = username
            fn.assign_output_paths(video)

        video.file_size = await self._get_file_size(download_url)
        video.download_link = download_url

        console.print(f"Download link retrieved for {video.video_id} (@{video.username})")

        return video

    async def _get_file_size(self, download_url: str) -> float:
        async with aiohttp.ClientSession() as session, session.get(download_url) as response:
            response.raise_for_status()
            total_size_bytes = float(response.headers.get("content-length", 0))
            return total_size_bytes  # noqa: RET504
