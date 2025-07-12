from playwright.sync_api import Playwright
import requests

from tikorgzo.console import console
from tikorgzo.core.video_info import FileSize, VideoInfo
from tikorgzo.exceptions import HrefLinkMissingError, HtmlElementMissingError, URLParsingError

TIKTOK_DOWNLOADER_URL = r"https://www.tikwm.com/originalDownloader.html"


class Browser:
    def __init__(self, playwright: Playwright) -> None:
        self._browser = playwright.chromium.launch(headless=True)  # Set headless=True for no UI
        self._context = self._browser.new_context(accept_downloads=True)  # Crucial for downloads
        self._page = self._context.new_page()

    def open_webpage(self):
        with console.status("Opening webpage..."):
            self._page.goto(TIKTOK_DOWNLOADER_URL)
            self._page.wait_for_load_state("networkidle")

    def cleanup(self):
        self._context.close()
        self._browser.close()

    def submit_link(self, video_link: str) -> None:
        input_field_selector = "input#params"

        try:
            with console.status("Pasting video link..."):
                self._page.locator(input_field_selector).fill(video_link)
        except Exception as e:
            print(f"Error finding or filling input field with selector '{input_field_selector}': {e}")
            self._browser.close()
            exit(1)

        submit_button_selector = "button:has-text('Submit')"

        try:
            with console.status("Submitting link..."):
                self._page.locator(submit_button_selector).click()
        except Exception as e:
            print(f"Error finding or clicking submit button with selector '{submit_button_selector}': {e}")
            self._browser.close()
            exit(1)

    def get_download_link(self, vid_info: VideoInfo) -> VideoInfo:
        download_link_selector = "a:has-text('Watermark')"
        parsing_error_selector = "div:has-text('Url parsing is failed!')"
        general_error_selector = "div:has-text('error')"

        with console.status("Waiting for download link..."):
            self._page.wait_for_selector(f"{download_link_selector}, {parsing_error_selector}, {general_error_selector}", state="visible", timeout=60000)

            if self._page.query_selector(parsing_error_selector) or self._page.query_selector(general_error_selector):
                raise URLParsingError()

            download_element = self._page.query_selector(download_link_selector)
            if download_element is None:
                raise HtmlElementMissingError(download_link_selector)

        download_url = download_element.get_attribute('href')
        if download_url:
            h4_elements = self._page.locator("h4")
            username = h4_elements.nth(2).inner_text()

            if vid_info.username is None:
                vid_info.username = username
                vid_info._process_output_paths()
            vid_info.file_size = self._get_file_size(download_url)
            vid_info.download_link = download_url

            return vid_info
        else:
            raise HrefLinkMissingError()

    def _get_file_size(self, download_url: str) -> FileSize:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        total_size_bytes = int(response.headers.get('content-length', 0))
        file_size_obj = FileSize(total_size_bytes)

        return file_size_obj
