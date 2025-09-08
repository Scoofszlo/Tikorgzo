import asyncio
import aiofiles
import aiohttp
from rich.progress import Progress

from tikorgzo.constants import DownloadStatus
from tikorgzo.core.video.model import Video


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
                video.download_status = DownloadStatus.COMPLETED
            except (asyncio.CancelledError, Exception):
                video.download_status = DownloadStatus.INTERRUPTED
