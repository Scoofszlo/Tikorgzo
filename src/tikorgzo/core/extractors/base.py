from abc import abstractmethod
import asyncio

from tikorgzo.core.extractors.constants import MAX_CONCURRENT_EXTRACTION_TASKS
from tikorgzo.core.video.model import Video


class BaseExtractor:
    """An interface to define extractor methods."""

    def __init__(self, extraction_delay: float) -> None:
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXTRACTION_TASKS)
        self._extraction_delay = extraction_delay
        self._delay_lock = asyncio.Lock()
        self._done_first_task = False

    @abstractmethod
    async def process_video_links(self, videos: list[Video]) -> list[Video | BaseException]:
        """Processes a list of video links and returns the results."""

    @abstractmethod
    async def cleanup(self) -> None:
        """ Cleans up any resources used by the extractor."""

    async def initialize(self) -> None:
        """Initializes any resources needed by the extractor."""
