import asyncio
import pathlib

import requests
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn

from tikorgzo.console import console
from tikorgzo.constants import DIRECT_EXTRACTOR_NAME, TIKWM_EXTRACTOR_NAME, DownloadStatus
from tikorgzo.core.download_manager.downloader import Downloader
from tikorgzo.core.extractors.direct.extractor import DirectExtractor
from tikorgzo.core.extractors.tikwm.extractor import TikWMExtractor
from tikorgzo.core.video.model import Video
from tikorgzo.exceptions import ExtractorCreationError, InvalidVideoLinkExtractionError


def extract_video_links(file_path: str | None, links: list[str]) -> set[str]:
    """Extracts the video links based from a list of strings or from a file."""

    if file_path:
        try:
            with pathlib.Path(file_path).open("r", encoding="utf-8") as f:
                return {line.strip() for line in f if line.strip()}
        except FileNotFoundError as e:
            raise FileNotFoundError from e

    elif links:
        return set(links)

    raise InvalidVideoLinkExtractionError


def get_extractor(
        extractor: str,
        extraction_delay: float,
        session: requests.Session | aiohttp.ClientSession,
) -> "TikWMExtractor | DirectExtractor":
    if extractor == TIKWM_EXTRACTOR_NAME:
        return TikWMExtractor(extraction_delay)
    if extractor == DIRECT_EXTRACTOR_NAME and isinstance(session, requests.Session):
        return DirectExtractor(extraction_delay, session)
    raise ExtractorCreationError


async def download_video(
    max_concurrent_downloads: int | None,
    videos: list[Video],
    session: requests.Session | aiohttp.ClientSession,
) -> list[Video]:
    """Download all the videos from queue that has the list of Video instances."""

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress_displayer:
        async with Downloader(session, max_concurrent_downloads) as downloader:
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
                # Temporarily disable the recommendation here to remove return in finally block
                # as this cause issues with downloader.py
                return videos  # noqa: B012 # pylint: disable=lost-exception, return-in-finally


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
