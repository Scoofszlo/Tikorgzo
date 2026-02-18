import aiofiles
import aiohttp
from rich.progress import Progress

from tikorgzo.constants import DownloadStatus
from tikorgzo.core.download_manager.constants import CHUNK_SIZE, STATUS_OK
from tikorgzo.core.download_manager.strategies._base import BaseDownloadStrategy
from tikorgzo.core.video.model import Video


class AioHTTPDownloadStrategy(BaseDownloadStrategy):
    """Downloads a video using an aiohttp session."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session

    async def download(self, video: Video, progress: Progress) -> None:
        async with self.session.get(video.download_link) as response:
            if response.status != STATUS_OK:
                video.download_status = DownloadStatus.INTERRUPTED
                msg = f"[gray50]Failed to download {video.video_id} due to[/gray50]: [orange1]{response.status} status code[/orange1]"
                progress.console.print(msg)
                return

            total_size = video.file_size.get()
            assert isinstance(total_size, float)

            task = progress.add_task(str(video.video_id), total=total_size)
            async with aiofiles.open(video.output_file_path, "wb") as output_file:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    if chunk:
                        await output_file.write(chunk)
                        progress.update(task, advance=len(chunk))

            video.download_status = DownloadStatus.COMPLETED
