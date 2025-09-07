import asyncio
from typing import Optional
import aiofiles
import aiohttp
import requests
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from tikorgzo.console import console
from tikorgzo.core.video.model import FileSize, Video
from tikorgzo.exceptions import DownloadError


class Downloader:
    def __init__(self) -> None:
        self.semaphore = asyncio.Semaphore(5)

    async def __aenter__(self) -> 'Downloader':
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            await self.session.close()

    async def download(self, video: Video, progress_displayer: Progress) -> None:
        async with self.semaphore:
            try:
                async with self.session.get(video.download_link) as response:
                    total_size = video.file_size.get()

                    assert isinstance(total_size, int)

                    task = progress_displayer.add_task(str(video.video_id), total=total_size)
                    async with aiofiles.open(video.output_file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            if chunk:
                                await file.write(chunk)
                                progress_displayer.update(task, advance=len(chunk))

            except Exception as e:
                raise DownloadError(e)
