import aiofiles
import aiohttp
import asyncio
from rich.progress import Progress
from typing import Optional

from tikorgzo.constants import DownloadStatus
from tikorgzo.core.video.model import Video


class Downloader:
    def __init__(self, max_concurrent_downloads: Optional[int] = None) -> None:
        self.semaphore = asyncio.Semaphore(4) if max_concurrent_downloads is None else asyncio.Semaphore(max_concurrent_downloads)

    async def __aenter__(self) -> 'Downloader':
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:
        if self.session:
            await self.session.close()

    async def download(self, video: Video, progress_displayer: Progress) -> None:
        async with self.semaphore:
            try:
                async with self.session.get(video.download_link) as response:
                    total_size = video.file_size.get()

                    assert isinstance(total_size, float)

                    task = progress_displayer.add_task(str(video.video_id), total=total_size)
                    async with aiofiles.open(video.output_file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            if chunk:
                                await file.write(chunk)
                                progress_displayer.update(task, advance=len(chunk))
                video.download_status = DownloadStatus.COMPLETED
            except (asyncio.CancelledError, Exception):
                video.download_status = DownloadStatus.INTERRUPTED
                raise
