import asyncio
import sys
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from typing import List, Optional

from tikorgzo.console import console
from tikorgzo.constants import DownloadStatus
from tikorgzo.core.download_manager.downloader import Downloader
from tikorgzo.core.video.model import Video
from tikorgzo.exceptions import InvalidLinkSourceExtractionError


def extract_video_links(file_path: Optional[str], links: List[str]) -> set[str]:
    """Extracts the video links based from a list of strings or from a file. """

    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return set([line.strip() for line in f if line.strip()])
        except FileNotFoundError:
            console.print(f"[red]error[/red]: '{file_path}' doesn't exist.")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]error[/red]: {e}")
            sys.exit(1)

    elif links:
        links_list = []

        for link in links:
            links_list.append(link)

        return set(links_list)

    raise InvalidLinkSourceExtractionError()


async def download_video(
    max_concurrent_downloads: Optional[int],
    videos: list[Video]
) -> list[Video]:
    """Download all the videos from queue that has the list of Video instances."""

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress_displayer:
        async with Downloader(max_concurrent_downloads) as downloader:
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


def cleanup_interrupted_downloads(videos: list[Video]) -> None:
    import os
    with console.status("Cleaning up unfinished files..."):
        for video in videos:
            if video.download_status == DownloadStatus.INTERRUPTED and os.path.exists(video.output_file_path):
                os.remove(video.output_file_path)


def print_download_results(videos: list[Video]) -> None:
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
