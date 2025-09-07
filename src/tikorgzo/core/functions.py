import asyncio
from typing import List
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from tikorgzo.core.extractor import Extractor
from tikorgzo.core.download_manager.downloader import Downloader
from tikorgzo.core.video.model import Video


async def extract_download_link(videos: List[Video]) -> List[Video]:
    """Extracts and gets the download link for the given Video instance."""

    async with Extractor() as ext:
        await ext.process_video_links(videos)

    return videos


async def download_video(videos: list[Video]) -> None:
    """Download all the videos from queue that has the list of Video instances."""

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress_displayer:
        async with Downloader() as downloader:
            download_tasks = [downloader.download(video, progress_displayer) for video in videos]
            await asyncio.gather(*download_tasks)
