import asyncio
from typing import Optional
import aiohttp
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from tikorgzo.console import console
from tikorgzo.core.video.model import Video
from tikorgzo.exceptions import HrefLinkMissingError, HtmlElementMissingError, URLParsingError

TIKTOK_DOWNLOADER_URL = r"https://www.tikwm.com/originalDownloader.html"


class Extractor:
    """Uses Playwright to browse the API for download link extraction."""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.semaphore = asyncio.Semaphore(5)  # Handles 

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(accept_downloads=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    async def process_video_links(self, videos: list[Video]) -> list[Video | BaseException]:
        tasks = [self._extract(video) for video in videos]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _extract(self, video: Video) -> Video:
        # The code is wrapped inside the semaphore so that a maximum number of tasks will be handled
        # at a time
        async with self.semaphore:
            try:
                assert isinstance(self.context, BrowserContext)

                page: Page = await self.context.new_page()

                await self._open_webpage(page)
                await self._submit_link(page, video.video_link)
                video = await self._get_download_link(page, video)
                await page.close()

                return video
            except (
                HrefLinkMissingError,
                HtmlElementMissingError,
                URLParsingError,
            ) as e:
                console.print(f"Skipping {video.video_id} due to: [red]{type(e).__name__}: {e}[/red]")
                # Needs to re-raise so that the mainline script (main.py) will caught this exception
                # thus, the program can filter tasks that are successful and not these failed tasks
                # due to these exception
                raise e

    async def _open_webpage(self, page: Page):
        await page.goto(TIKTOK_DOWNLOADER_URL)
        await page.wait_for_load_state("networkidle")

    async def _submit_link(self, page: Page, video_link: str) -> None:
        input_field_selector = "input#params"

        try:
            await page.locator(input_field_selector).fill(video_link)
        except Exception:
            raise HtmlElementMissingError(input_field_selector)

        submit_button_selector = "button:has-text('Submit')"

        while True:
            try:
                await page.locator(submit_button_selector).click()
            except Exception:
                raise HtmlElementMissingError(submit_button_selector)

            # Wait for either the limit message or the next step to appear
            limit_selector = "div:has-text('Free Api Limit: 1 request/second.')"
            try:
                # Wait briefly to see if the limit message appears
                await page.wait_for_selector(limit_selector, state="visible", timeout=2000)
                # If limit message appears, wait and retry
                await asyncio.sleep(1)
                continue
            except Exception:
                # If limit message does not appear, break loop
                break

    async def _get_download_link(self, page: Page, video: Video) -> Video:
        download_link_selector = "a:has-text('Watermark')"
        parsing_error_selector = "div:has-text('Url parsing is failed!')"
        general_error_selector = "div:has-text('error')"

        await page.wait_for_selector(f"{download_link_selector}, {parsing_error_selector}, {general_error_selector}", state="visible", timeout=60000)

        if await page.query_selector(parsing_error_selector) or await page.query_selector(general_error_selector):
            raise URLParsingError()

        download_element = await page.query_selector(download_link_selector)

        if download_element is None:
            raise HtmlElementMissingError(download_link_selector)

        download_url = await download_element.get_attribute('href')

        if not download_url:
            raise HrefLinkMissingError()

        # Username is scraped here in case that the Video instance doesn't have a username
        # yet. This is important so that the videos are grouped by username when downloaded.
        h4_elements = page.locator("h4")
        username = await h4_elements.nth(2).inner_text()

        if video.username is None:
            from tikorgzo.core.video.processor import VideoInfoProcessor
            processor = VideoInfoProcessor()

            video.username = username
            processor.process_output_paths(video)

        video.file_size = await self._get_file_size(download_url)
        video.download_link = download_url

        console.print(f"Download link retrieved for {video.video_id} (@{video.username})")

        return video

    async def _get_file_size(self, download_url: str) -> int:
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                response.raise_for_status()
                total_size_bytes = int(response.headers.get('content-length', 0))
                return total_size_bytes
