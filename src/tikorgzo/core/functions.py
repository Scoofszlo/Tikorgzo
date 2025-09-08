import asyncio
from typing import List
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from tikorgzo.console import console
from tikorgzo.constants import DownloadStatus
from tikorgzo.core.extractor import Extractor
from tikorgzo.core.download_manager.downloader import Downloader
from tikorgzo.core.video.model import Video


async def extract_download_link(videos: List[Video]) -> List[Video]:
    """Extracts and gets the download link for the given Video instance."""

    async with Extractor() as ext:
        await ext.process_video_links(videos)

    return videos


async def download_video(videos: list[Video]) -> list[Video]:
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
            try:
                await asyncio.gather(*download_tasks)
                return videos
            except asyncio.CancelledError:
                await asyncio.gather(*download_tasks, return_exceptions=True)
                for video in videos:
                    if video.download_status != DownloadStatus.COMPLETED:
                        video.download_status = DownloadStatus.INTERRUPTED
                return videos


def print_download_results(videos: list[Video]):
    failed_downloads = 0
    successful_downloads = 0

    for video in videos:
        if video.download_status == DownloadStatus.INTERRUPTED:
            failed_downloads += 1
        elif video.download_status == DownloadStatus.COMPLETED:
            successful_downloads += 1

    if failed_downloads == 0:
        console.print(f"\nFinished downloads with [green]{successful_downloads} success[/green]")
    elif successful_downloads == 0 and failed_downloads >= 1:
        console.print(f"\nFinished downloads with [red]{failed_downloads} failed[/red]")
    elif failed_downloads >= 1:
        console.print(f"\nFinished downloads with [green]{successful_downloads} successful[/green], [red]{failed_downloads} failed[/red]")
