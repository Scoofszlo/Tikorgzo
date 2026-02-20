import asyncio
from pathlib import Path

import requests
from requests import HTTPError
from rich.progress import Progress

from tikorgzo.constants import STATUS_OK, DownloadStatus
from tikorgzo.core.download_manager.constants import CHUNK_SIZE
from tikorgzo.core.download_manager.strategies._base import BaseDownloadStrategy
from tikorgzo.core.video.model import Video


class RequestsDownloadStrategy(BaseDownloadStrategy):
    """Downloads a video using a requests session."""

    def __init__(self, session: requests.Session) -> None:
        self.session = session

    async def download(self, video: Video, progress: Progress) -> None:
        def start() -> None:
            try:
                response = self.session.get(video.download_link, stream=True)

                if response.status_code != STATUS_OK:
                    video.download_status = DownloadStatus.INTERRUPTED
                    self._print_failed_status(video, response.status_code, progress)
                    return

                total_size = video.file_size.get()
                assert isinstance(total_size, float)

                task = progress.add_task(str(video.video_id), total=total_size)
                with Path.open(video.output_file_path, "wb", encoding=None) as output_file:  # pylint: disable=unspecified-encoding
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            output_file.write(chunk)
                            progress.update(task, advance=len(chunk))

                video.download_status = DownloadStatus.COMPLETED
            except (HTTPError, Exception):
                video.download_status = DownloadStatus.INTERRUPTED
                raise

        await asyncio.to_thread(start)
