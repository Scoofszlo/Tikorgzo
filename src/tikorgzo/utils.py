import logging
import os
from typing import Optional

from tikorgzo.core.video.model import Video
from tikorgzo.exceptions import InvalidLinkSourceExtractionError


def setup_logging():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S%z'
    )
    handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler]
    )


def video_link_extractor(file_path: str, links: str) -> list[str]:
    """Extracts the video ID of a TikTok video based from a list of strings."""

    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    elif links:
        links_list = []

        for link in links:
            links_list.append(link)

        return links_list

    raise InvalidLinkSourceExtractionError()


def remove_file(video: Optional[Video]) -> None:
    if video is None:
        return

    try:
        os.remove(video.output_file_path)
    except FileNotFoundError:
        return
