

import asyncio

from playwright.async_api import Browser, BrowserContext, Page, Playwright, ProxySettings, async_playwright

from tikorgzo.constants import CHROME_USER_DATA_DIR
from tikorgzo.exceptions import MissingChromeBrowserError


class ScrapeBrowser:
    """Manages the initialization and cleanup of a Playwright browser instance that
    will be used for getting download links from TikWM API.
    """

    def __init__(self, proxy: str | None = None) -> None:
        self._proxy = proxy
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def initialize(self) -> None:
        """Initializes the Playwright browser instance."""

        if self._proxy:
            proxy: ProxySettings | None = {
                "server": "https://" + self._proxy,
                "bypass": None,
                "username": None,
                "password": None,
            }
        else:
            proxy = None

        try:
            self._playwright = await async_playwright().start()
            self.context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=CHROME_USER_DATA_DIR,
                channel="chrome",
                headless=False,
                accept_downloads=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                ],
                viewport={"width": 500, "height": 200},
                proxy=proxy,
            )
        except asyncio.CancelledError:
            await asyncio.sleep(1)
            await self.cleanup()

            raise
        except Exception as e:
            await self.cleanup()

            if "Executable doesn't exist" in str(e) or "'chrome is not found" in str(e):
                raise MissingChromeBrowserError from None
            raise e  # noqa: TRY201

    async def cleanup(self) -> None:
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
