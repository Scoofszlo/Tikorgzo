from playwright.sync_api import Playwright

from tikorgzo.core.browser import Browser
from tikorgzo.core.video_info import VideoInfo


TIKTOK_DOWNLOADER_URL = r"https://www.tikwm.com/originalDownloader.html"
browser: Browser


class MetadataExtractor:
    def __init__(self, playwright: Playwright) -> None:
        global browser
        browser = Browser(playwright=playwright)
        print("Intialized")

    def extract_metadata(self, vid_info: VideoInfo) -> VideoInfo:
        browser.open_webpage()
        browser.submit_link(vid_info.video_link)
        vid_info = browser.get_download_link(vid_info)
        browser.cleanup()

        return vid_info
