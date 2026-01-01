from abc import abstractmethod
import asyncio

from tikorgzo.core.extractors.constants import MAX_CONCURRENT_EXTRACTION_TASKS
from tikorgzo.core.video.model import Video


class BaseExtractor:
    """An interface to define extractor methods."""

    def __init__(self) -> None:
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXTRACTION_TASKS)

    @abstractmethod
    async def process_video_links(self, videos: list[Video]) -> list[Video | BaseException]:
        """Processes a list of video links and returns the results."""

    @abstractmethod
    async def cleanup(self) -> None:
        """ Cleans up any resources used by the extractor."""

    async def initialize(self) -> None:
        """Initializes any resources needed by the extractor."""
