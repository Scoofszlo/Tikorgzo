
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from tikorgzo.constants import CHROME_USER_DATA_DIR
from tikorgzo.exceptions import MissingChromeBrowserError, MissingPlaywrightBrowserError


class ScrapeBrowser:
    """A class for Playwright browser instance management."""

    def __init__(self) -> 'ScrapeBrowser':
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize(self) -> 'ScrapeBrowser':
        """Initializes the Playwright browser instance."""

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
                viewport={'width': 500, 'height': 200},
            )
        except Exception as e:
            if hasattr(self, 'browser') and self._browser:
                await self._browser.close()
            if hasattr(self, 'playwright') and self._playwright:
                await self._playwright.stop()

            if "Executable doesn't exist" or "'chrome is not found" in str(e):
                raise MissingChromeBrowserError()
            else:
                raise e

    async def cleanup(self) -> None:
        if self._browser:
            await self._browser.close()
        await self._playwright.stop()
