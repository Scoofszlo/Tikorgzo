from abc import ABC, abstractmethod

from rich.progress import Progress

from tikorgzo.core.video.model import Video


class BaseDownloadStrategy(ABC):
    """Abstract base model for download strategies."""

    @abstractmethod
    async def download(self, video: Video, progress: Progress) -> None:
        """Download the video and update the progress display."""

    @staticmethod
    def _print_failed_status(video: Video, status_code: int, progress: Progress) -> None:
        """Print a message when a download fails due to a non-OK status code."""
        msg = f"[gray50]Failed to download {video.video_id} due to[/gray50]: [orange1]{status_code} status code[/orange1]"
        progress.console.print(msg)
