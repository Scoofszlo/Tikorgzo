from typing import List

from tikorgzo.core.extractor import Extractor
from tikorgzo.core.downloader import Downloader
from tikorgzo.core.video.model import Video


async def extract_download_link(videos: List[Video]) -> List[Video]:
    """Extracts and gets the download link for the given Video instance."""

    async with Extractor() as ext:
        await ext.process_video_links(videos)

    return videos


def download_video(video: Video) -> None:
    """Download the video using the provided Video instance."""

    downloader = Downloader()

    downloader.download(
        video.download_link,
        video.output_file_path,
        video.file_size
    )
