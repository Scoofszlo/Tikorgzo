

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from tikorgzo.constants import CHROME_USER_DATA_DIR
from tikorgzo.exceptions import MissingChromeBrowserError


class ScrapeBrowser:
    """Manages the initialization and cleanup of a Playwright browser instance that
    will be used for getting download links from TikWM API.
    """

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def initialize(self) -> None:
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
                viewport={"width": 500, "height": 200},
            )
        except Exception as e:
            if hasattr(self, "browser") and self._browser:
                await self._browser.close()
            if hasattr(self, "playwright") and self._playwright:
                await self._playwright.stop()

            if "Executable doesn't exist" in str(e) or "'chrome is not found" in str(e):
                raise MissingChromeBrowserError from None
            raise e  # noqa: TRY201

    async def cleanup(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
