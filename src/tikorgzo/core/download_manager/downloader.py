import aiofiles
import aiohttp
import asyncio
from requests import Session, HTTPError

from rich.progress import Progress
from typing import Optional

from tikorgzo.constants import DownloadStatus
from tikorgzo.core.video.model import Video


class Downloader:
    def __init__(
            self,
            session: Optional[Session] = None,
            max_concurrent_downloads: Optional[int] = None,
    ) -> None:
        self.session = session if session else aiohttp.ClientSession()
        self.semaphore = asyncio.Semaphore(4) if max_concurrent_downloads is None else asyncio.Semaphore(max_concurrent_downloads)

    async def __aenter__(self) -> 'Downloader':
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:
        if self.session and isinstance(self.session, aiohttp.ClientSession):
            await self.session.close()

    async def download(self, video: Video, progress_displayer: Progress) -> None:
        if isinstance(self.session, aiohttp.ClientSession):
            async with self.semaphore:
                try:
                    async with self.session.get(video.download_link) as aio_response:
                        if aio_response.status != 200:
                            video.download_status = DownloadStatus.INTERRUPTED
                            raise aiohttp.ClientResponseError(
                                request_info=aio_response.request_info,
                                history=aio_response.history,
                                status=aio_response.status,
                                message=f"Failed to download video: {aio_response.status}",
                                headers=aio_response.headers
                            )

                        total_size = video.file_size.get()

                        assert isinstance(total_size, float)

                        task = progress_displayer.add_task(str(video.video_id), total=total_size)
                        async with aiofiles.open(video.output_file_path, 'wb') as file:
                            async for chunk in aio_response.content.iter_chunked(8192):
                                if chunk:
                                    await file.write(chunk)
                                    progress_displayer.update(task, advance=len(chunk))
                    video.download_status = DownloadStatus.COMPLETED
                except (asyncio.CancelledError, Exception):
                    video.download_status = DownloadStatus.INTERRUPTED
                    raise
        elif isinstance(self.session, Session):
            print(f"Using requests.Session for downloading video ID: {video.video_id}")
            req_response = self.session.get(video.download_link, stream=True)
            try:
                if req_response.status_code != 200:
                    video.download_status = DownloadStatus.INTERRUPTED
                    print(f"Failed to download video: {req_response.status_code}")
                    raise HTTPError(f"Failed to download video: {req_response.status_code}")

                total_size = video.file_size.get()

                assert isinstance(total_size, float)

                task = progress_displayer.add_task(str(video.video_id), total=total_size)
                with open(video.output_file_path, 'wb') as file:
                    for chunk in req_response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            progress_displayer.update(task, advance=len(chunk))
                video.download_status = DownloadStatus.COMPLETED
            finally:
                aio_response.close()
                self.session.close()
