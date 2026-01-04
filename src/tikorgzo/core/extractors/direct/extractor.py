import asyncio
import json
from typing import Optional

from bs4 import BeautifulSoup
import requests
from tikorgzo.core.extractors.base import BaseExtractor
from tikorgzo.core.extractors.direct.helpers import (
    get_initial_url,
    get_download_addresses,
    get_best_quality,
)
from tikorgzo.console import console
from tikorgzo.core.video.model import Video
from tikorgzo.core.video.processor import VideoInfoProcessor
from tikorgzo.exceptions import APIStructureMismatchError, MissingSourceDataError


class DirectExtractor(BaseExtractor):
    """Extractor that handles download link extraction directly from TikTok
    site."""
    def __init__(self, delay: float, session: requests.Session) -> None:
        self.session = session
        super().__init__(delay)

    async def process_video_links(self, videos: list[Video]) -> list[Video | BaseException]:
        tasks = [self._extract(video) for video in videos]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def cleanup(self) -> None:
        self.session.close()

    async def _extract(self, video: Video) -> Video:
        # Add delay between link extraction to limit rate of requests
        # being sent
        async with self._delay_lock:
            if self._done_first_task:
                await asyncio.sleep(self._extraction_delay)
            else:
                self._done_first_task = True

        try:
            url = await self._get_url(video.video_link)
            source_data = await self._get_source_data(self.session, url)
            best_quality_details = await self._get_best_quality_details(source_data)
            download_link = best_quality_details["PlayAddr"]["UrlList"][1]
            username = await self._get_username(source_data)

            if video.username is None:
                processor = VideoInfoProcessor()

                video.username = username
                processor.process_output_paths(video)

            video.download_link = download_link
            video.file_size = float(best_quality_details["PlayAddr"]["DataSize"])

            console.print(f"Download link retrieved for {video.video_id} (@{video.username})")

            return video
        except Exception as e:
            console.print(f"Skipping {video.video_id} due to: [red]{type(e).__name__}: {e}[/red]")
            raise e

    async def _get_url(
            self,
            video_link: str,
    ) -> str:
        video_url: Optional[str] = None

        if len(video_link) == 19 and video_link.isdigit():
            video_url = get_initial_url(video_link)
        else:
            video_url = video_link

        return video_url

    async def _get_source_data(self, session: requests.Session, url: str) -> dict:
        """Gets the content of the script tag that contains the initial
        data"""

        response = session.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find("script", id="__UNIVERSAL_DATA_FOR_REHYDRATION__")

        if script_tag is None or script_tag.string is None:
            raise MissingSourceDataError("Script tag with id '__UNIVERSAL_DATA_FOR_REHYDRATION__' not found")

        data = json.loads(script_tag.string)
        script_content_as_json = data

        return script_content_as_json

    async def _get_best_quality_details(
            self,
            data: dict
    ) -> dict:
        try:
            download_addresses = await get_download_addresses(data)
            best_quality_details = await get_best_quality(download_addresses)

            return best_quality_details
        except Exception as e:
            raise e

    async def _get_username(self, data: dict) -> str:
        try:
            path_to_username = [
                "__DEFAULT_SCOPE__",
                "webapp.video-detail",
                "itemInfo",
                "itemStruct",
                "author",
                "uniqueId"
            ]

            current = data

            for i, key in enumerate(path_to_username):
                try:
                    current = current[key]
                except (KeyError, TypeError) as e:
                    # i + 1 shows how deep we got
                    broken_path = " -> ".join(path_to_username[:i+1])
                    raise APIStructureMismatchError(f"Data containing username from API is missing or may have changed. Failed at {broken_path}") from e
            return str(current)
        except Exception as e:
            raise e
