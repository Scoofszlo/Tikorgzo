from playwright.sync_api import sync_playwright

from tikorgzo.core.downloader import Downloader
from tikorgzo.core.extractor import MetadataExtractor
from tikorgzo.core.video_info import VideoInfo


def update_metadata(vid_info: VideoInfo) -> VideoInfo:
    """Extracts and updates the metadata for the given video."""

    with sync_playwright() as p:
        extractor = MetadataExtractor(p)
        vid_info = extractor.extract_metadata(vid_info)

    return vid_info


def download_video(video_info: VideoInfo) -> None:
    """Download the video using the provided VideoInfo."""

    downloader = Downloader()

    downloader.download(
        video_info.download_link,
        video_info.output_file_path,
        video_info.file_size
    )
