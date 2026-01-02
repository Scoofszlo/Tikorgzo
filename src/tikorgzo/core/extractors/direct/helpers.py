import aiohttp
from tikorgzo.exceptions import APIChangeError

URL_TEMPLATE = "https://m.tiktok.com/v/{}.html"


def get_initial_url(video_id: str) -> str:
    """Gets the initial URL by applying the video ID to the URL template.
    """

    return URL_TEMPLATE.format(video_id)


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
