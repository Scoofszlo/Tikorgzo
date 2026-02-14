from types import TracebackType
from typing import Self

from tikorgzo.core.extractors.base import BaseExtractor
from tikorgzo.core.video.model import Video


class ExtractorHandler:
    """A context manager to handle usage and cleanup of extractor."""

    def __init__(self, extractor: BaseExtractor, disallow_cleanup: bool = False) -> None:
        self.extractor: BaseExtractor = extractor
        self.disallow_cleanup = disallow_cleanup

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        if not self.disallow_cleanup:
            await self.extractor.cleanup()

    async def process_video_links(self, videos: list[Video]) -> list[Video | BaseException]:
        return await self.extractor.process_video_links(videos)
