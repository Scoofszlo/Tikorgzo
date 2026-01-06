import aiohttp
from tikorgzo.exceptions import APIStructureMismatchError

URL_TEMPLATE = "https://m.tiktok.com/v/{}.html"


def get_initial_url(video_id: str) -> str:
    """Gets the initial URL by applying the video ID to the URL template.
    """

    return URL_TEMPLATE.format(video_id)


async def get_download_addresses(data: dict) -> list[dict]:
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
            raise APIStructureMismatchError(f"Data containing download addresses from API is missing or may have changed. Failed at {broken_path}") from e

    try:
        # Assert that data is a list (specifically a list of dicts). If AssertionError
        # happens, this means the API structure for this data may have changed.
        assert isinstance(current, list)
        return current
    except AssertionError as e:
        raise APIStructureMismatchError("Download addresses data from API is not in expected format.") from e

async def get_best_quality(download_addresses: list[dict]) -> dict:
    """Gets the best quality download link from the download addresses
    dict."""

    def quality_score(item: dict):
        width = item.get("PlayAddr", {}).get("Width", 0)
        height = item.get("PlayAddr", {}).get("Height", 0)
        resolution = width * height

        bitrate = item.get("Bitrate", 0)

        return (resolution, bitrate)

    best_quality = max(download_addresses, key=quality_score)
    return best_quality
