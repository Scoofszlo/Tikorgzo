from playwright.sync_api import Playwright, TimeoutError, Error

from tikorgzo.core.browser import Browser
from tikorgzo.core.video.model import Video
from tikorgzo.exceptions import ExtractionTimeoutError


TIKTOK_DOWNLOADER_URL = r"https://www.tikwm.com/originalDownloader.html"


class DownloadLinkExtractor:
    """Extracts the download link from the API."""

    def __init__(self, playwright: Playwright) -> None:
        self.browser = Browser(playwright=playwright)

    def extract_download_link(self, video: Video) -> Video:
        """Returns the Video instance with the downloadable link of the video."""
        try:
            self.browser.open_webpage()
            self.browser.submit_link(video.video_link)
            video = self.browser.get_download_link(video)
            self.browser.cleanup()

            return video
        except TimeoutError:
            raise ExtractionTimeoutError()
