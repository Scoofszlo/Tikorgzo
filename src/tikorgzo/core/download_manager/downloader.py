import asyncio
from types import TracebackType
from typing import Self

import aiofiles
import aiohttp
import anyio
import requests
from requests import HTTPError
from rich.progress import Progress

from tikorgzo.console import console
from tikorgzo.constants import DownloadStatus
from tikorgzo.core.video.model import Video


class Downloader:
    def __init__(
        self,
        session: requests.Session | aiohttp.ClientSession,
        max_concurrent_downloads: int | None = None,
    ) -> None:
        self.session = session
        self.semaphore = asyncio.Semaphore(4) if max_concurrent_downloads is None else asyncio.Semaphore(max_concurrent_downloads)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        pass

    async def download(self, video: Video, progress_displayer: Progress) -> None:
        status_ok = 200

        if isinstance(self.session, aiohttp.ClientSession):
            async with self.semaphore:
                try:
                    async with self.session.get(video.download_link) as aio_response:
                        if aio_response.status != status_ok:
                            video.download_status = DownloadStatus.INTERRUPTED
                            raise aiohttp.ClientResponseError(  # noqa: TRY301
                                request_info=aio_response.request_info,
                                history=aio_response.history,
                                status=aio_response.status,
                                message=f"Failed to download {video.video_id}: {aio_response.status}",
                                headers=aio_response.headers,
                            )

                        total_size = video.file_size.get()

                        assert isinstance(total_size, float)

                        task = progress_displayer.add_task(str(video.video_id), total=total_size)
                        async with aiofiles.open(video.output_file_path, "wb") as file:
                            async for chunk in aio_response.content.iter_chunked(8192):
                                if chunk:
                                    await file.write(chunk)
                                    progress_displayer.update(task, advance=len(chunk))
                    video.download_status = DownloadStatus.COMPLETED
                except (asyncio.CancelledError, Exception):
                    video.download_status = DownloadStatus.INTERRUPTED
                    raise
        else:
            req_response = self.session.get(video.download_link, stream=True)
            try:
                if req_response.status_code != status_ok:
                    video.download_status = DownloadStatus.INTERRUPTED
                    console.print(f"Failed to download {video.video_id}: {req_response.status_code}")
                    msg = f"Failed to download {video.video_id}: {req_response.status_code}"
                    raise HTTPError(msg)  # noqa: TRY301

                total_size = video.file_size.get()

                assert isinstance(total_size, float)

                task = progress_displayer.add_task(str(video.video_id), total=total_size)
                async with await anyio.open_file(video.output_file_path, "wb") as file:
                    for chunk in req_response.iter_content(chunk_size=8192):
                        if chunk:
                            await file.write(chunk)
                            progress_displayer.update(task, advance=len(chunk))
                video.download_status = DownloadStatus.COMPLETED
            except (asyncio.CancelledError, Exception):
                video.download_status = DownloadStatus.INTERRUPTED
                raise
