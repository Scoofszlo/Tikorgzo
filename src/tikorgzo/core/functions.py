import asyncio
import os
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
            # The number of download tasks may not necesarilly equal to the total number of videos
            # that you want to download as it will depends on the number of the semaphore of the Downloader.
            # For example, if you have 50 total videos to download and you haave semaphore set to 5,
            # the tasks that will be processed at a time are 5 only. If the download was cancelled using Ctrl+C,
            # the remaining tasks that was not processed will be discarded. This means the
            # `download_tasks` will only contain Video instances that have been processed only.

            download_tasks = [downloader.download(video, progress_displayer) for video in videos]
            try:
                await asyncio.gather(*download_tasks)
            except asyncio.CancelledError:
                # This is needed to capture KeyboardInterrupt or the Ctrl+C thing as we all know.
                # However, there is nothing need to do here since the handle of this exception
                # is already done inisde the download() of our Downloader which assigns interrupted
                # status to the download status attribute of a Video instance
                pass
            finally:
                return videos


def cleanup_interrupted_downloads(videos: list[Video]):
    with console.status("Cleaning up unfinished files..."):
        for video in videos:
            if video.download_status == DownloadStatus.INTERRUPTED and os.path.exists(video.output_file_path):
                os.remove(video.output_file_path)


def print_download_results(videos: list[Video]):
    unstarted_downloads = 0
    failed_downloads = 0
    successful_downloads = 0
    result_msg = "\nFinished downloads with "
    use_comma_separator = False

    for video in videos:
        if video.download_status == DownloadStatus.QUEUED:
            unstarted_downloads += 1
        if video.download_status == DownloadStatus.INTERRUPTED:
            failed_downloads += 1
        elif video.download_status == DownloadStatus.COMPLETED:
            successful_downloads += 1

    if successful_downloads >= 1:
        result_msg += f"[green]{successful_downloads} successful[/green]"
        use_comma_separator = True
    if failed_downloads >= 1:
        if use_comma_separator:
            result_msg += f", [red]{failed_downloads} failed[/red]"
        else:
            result_msg += f"[red]{failed_downloads} failed[/red]"
            use_comma_separator = True
    if unstarted_downloads >= 1:
        if use_comma_separator:
            result_msg += f", [orange1]{unstarted_downloads} unstarted[/orange1]"
        else:
            result_msg += f"[orange1]{unstarted_downloads} unstarted[/orange1]"

    console.print(result_msg)
