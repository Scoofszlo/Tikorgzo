from abc import ABC, abstractmethod

from rich.progress import Progress

from tikorgzo.core.video.model import Video


class BaseDownloadStrategy(ABC):
    """Abstract base model for download strategies."""

    @abstractmethod
    async def download(self, video: Video, progress: Progress) -> None:
        """Download the video and update the progress display."""
