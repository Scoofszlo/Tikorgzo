from playwright.sync_api import sync_playwright

from tikorgzo.core.downloader import Downloader
from tikorgzo.core.extractor import DownloadLinkExtractor
from tikorgzo.core.video.model import Video


def extract_download_link(video: Video) -> Video:
    """Extracts and gets the download link for the given Video instance."""

    with sync_playwright() as p:
        extractor = DownloadLinkExtractor(p)
        video = extractor.extract_download_link(video)

    return video


def download_video(video: Video) -> None:
    """Download the video using the provided Video instance."""

    downloader = Downloader()

    downloader.download(
        video.download_link,
        video.output_file_path,
        video.file_size
    )
