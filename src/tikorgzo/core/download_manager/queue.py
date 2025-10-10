from tikorgzo.core.video.model import Video


class DownloadQueueManager:
    def __init__(self) -> None:
        self._queue: list[Video] = []

    def add(self, video: Video) -> None:
        self._queue.append(video)

    def total(self) -> int:
        return len(self._queue)

    def is_empty(self) -> bool:
        return len(self._queue) < 1

    def get_queue(self) -> list[Video]:
        return self._queue

    def replace_queue(self, videos: list[Video]) -> None:
        self._queue = videos
