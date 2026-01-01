import json
from bs4 import BeautifulSoup
from requests import Session

import aiohttp
from playwright.async_api import Page
from tikorgzo.exceptions import APIChangeError, MissingSourceDataError

URL_TEMPLATE = "https://m.tiktok.com/v/{}.html"


def get_initial_url(video_id: str) -> str:
    """Gets the initial URL by applying the video ID to the URL template.
    """

    return URL_TEMPLATE.format(video_id)


async def get_source_data(session: Session, url: str) -> dict:
    """Gets the content of the script tag that contains the initial
    data"""

    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    script_tag = soup.find("script", id="__UNIVERSAL_DATA_FOR_REHYDRATION__")

    if script_tag is None or script_tag.string is None:
        raise MissingSourceDataError(f"Script tag with id '__UNIVERSAL_DATA_FOR_REHYDRATION__' not found")

    data = json.loads(script_tag.string)
    script_content_as_json = data

    return script_content_as_json

async def get_download_addresses(data: dict):
    path_to_download_addrs = [
        "__DEFAULT_SCOPE__",
        "webapp.video-detail",
        "itemInfo",
        "itemStruct",
        "video",
        "bitrateInfo"
    ]

    current = data

    for i, key in enumerate(path_to_download_addrs):
        try:
            current = current[key]
        except (KeyError, TypeError) as e:
            # i + 1 shows how deep we got
            broken_path = " -> ".join(path_to_download_addrs[:i+1])
            raise APIChangeError(f"API structure has changed; cannot find download addresses. Failed at {broken_path}") from e

    return current

async def get_best_quality(download_addresses: dict) -> dict:
    """Gets the best quality download link from the download addresses
    dict."""

    def quality_score(item):
        # 1. Calculate total pixels (Resolution)
        width = item.get("PlayAddr", {}).get("Width", 0)
        height = item.get("PlayAddr", {}).get("Height", 0)
        resolution = width * height

        # 2. Get the Bitrate
        bitrate = item.get("Bitrate", 0)

        # Return a tuple: (Resolution, Bitrate)
        # Python's max() compares tuples element-by-element.
        # If Resolution is a tie, it looks at Bitrate.
        return (resolution, bitrate)

    best_quality = max(download_addresses, key=quality_score)
    return best_quality


async def get_file_size(download_url: str) -> float:
    """Gets the file size in bytes from the download URL."""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                response.raise_for_status()
                total_size_bytes = float(response.headers.get('content-length', 0))
                return total_size_bytes
    except Exception as e:
        raise e
