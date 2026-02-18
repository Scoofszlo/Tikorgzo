import asyncio
import os

import aiohttp
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn

from tikorgzo.console import console
from tikorgzo.constants import DownloadStatus
from tikorgzo.core.download_manager.strategies.aiohttp import AioHTTPDownloadStrategy
from tikorgzo.core.download_manager.strategies.requests import RequestsDownloadStrategy
from tikorgzo.core.session.model import ClientSessionManager
from tikorgzo.core.video.model import Video


class Downloader:
    def __init__(
        self,
        session: ClientSessionManager,
        videos: list[Video],
        max_concurrent_downloads: int | None = None,
    ) -> None:
        self.session = session
        self.videos = videos
        self.semaphore = asyncio.Semaphore(4) if max_concurrent_downloads is None else asyncio.Semaphore(max_concurrent_downloads)
        self.download_strategy = self._get_download_strategy()
        self.progress_displayer = Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        )

    async def process_videos(self) -> None:
        self.progress_displayer.start()
        download_tasks = [self.download(video) for video in self.videos]

        try:
            await asyncio.gather(*download_tasks)
        except asyncio.CancelledError:
            # This is needed to capture KeyboardInterrupt or the Ctrl+C thing as we all know.
            # However, there is nothing need to do here since the handle of this exception
            # is already done inisde the download() of our Downloader which assigns interrupted
            # status to the download status attribute of a Video instance
            pass
        finally:
            self.progress_displayer.stop()

    async def download(self, video: Video) -> None:
        async with self.semaphore:
            try:
                await self.download_strategy.download(video, self.progress_displayer)
            except (asyncio.CancelledError, Exception):
                video.download_status = DownloadStatus.INTERRUPTED
                raise

    def cleanup_interrupted_downloads(self) -> None:
        for video in self.videos:
            if video.download_status == DownloadStatus.INTERRUPTED and os.path.exists(video.output_file_path):
                os.remove(video.output_file_path)

    def _get_download_strategy(self) -> AioHTTPDownloadStrategy | RequestsDownloadStrategy:
        """Return the appropriate download strategy based on the session type."""

        if isinstance(self.session.client_session, aiohttp.ClientSession):
            return AioHTTPDownloadStrategy(self.session.client_session)
        return RequestsDownloadStrategy(self.session.client_session)
