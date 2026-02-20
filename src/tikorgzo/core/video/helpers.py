import os
import pathlib
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import requests

from tikorgzo.config.model import ConfigKey
from tikorgzo.constants import DEFAULT_DATE_FORMAT, DOWNLOAD_PATH, TIKTOK_ID_LENGTH
from tikorgzo.core.video.constants import IDEAL_BINARY_NUM_LEN, NORMAL_TIKTOK_VIDEO_LINK_REGEX, USERNAME_REGEX, VT_TIKTOK_VIDEO_LINK_REGEX
from tikorgzo.exceptions import InvalidDateFormatError, InvalidVideoLinkError, VideoFileAlreadyExistsError, VideoIDExtractionError

if TYPE_CHECKING:
    from tikorgzo.core.video.model import Video


def normalize_video_link(video_link: str, proxy: str | None = None) -> str:
    """Normalizes the TikTok video link into a standard format."""

    if re.search(NORMAL_TIKTOK_VIDEO_LINK_REGEX, video_link):
        return video_link

    if re.search(VT_TIKTOK_VIDEO_LINK_REGEX, video_link):
        return _get_normalized_url(video_link, proxy=proxy)

    if len(video_link) == TIKTOK_ID_LENGTH and video_link.isdigit():
        return video_link

    raise InvalidVideoLinkError(video_link)


def extract_video_id(video_link: str) -> int:
    """Extracts the video ID which is a 19-digit long that uniquely identifies a TikTok video."""
    match = re.search(r"/video/(\d+)", video_link)
    if match:
        return int(match.group(1))

    if len(video_link) == TIKTOK_ID_LENGTH and video_link.isdigit():
        return int(video_link)

    match = re.search(r"/(\d+)_original\.mp4", video_link)
    if match:
        return int(match.group(1))

    raise VideoIDExtractionError


def check_if_already_downloaded(
    video_id: int,
    lazy_duplicate_check: bool,
    custom_download_dir: str | None = None,
) -> None:
    """Recursively checks the output folder, which is the default
    DOWNLOAD_PATH, to see if a file already exists whether the filename
    contains the video ID or not. If true, this will raise an error.

    This function only runs when `--strict-duplicate-check` is enabled.
    """

    if lazy_duplicate_check is True:
        return

    download_dir = _get_download_dir(custom_download_dir)
    if not os.path.exists(download_dir):
        pathlib.Path(download_dir).mkdir(exist_ok=True, parents=True)

    for root, _, filenames in os.walk(download_dir):
        for f in filenames:
            if str(video_id) in f:
                username = pathlib.Path(root).name
                raise VideoFileAlreadyExistsError(f, username)


def process_username(video_link: str) -> str | None:
    """Some video links include username so this method processes those links
    and extracts the username from it.

    If nothing can be extracted, this returns None
    """
    match = re.search(USERNAME_REGEX, video_link)

    if match:
        return match.group(1)
    return None


def get_date(video_id: int) -> datetime:
    """Gets the date from the video ID.

    This one is pretty interesting as I read from this article
    (https://dfir.blog/tinkering-with-tiktok-timestamps/) that TikTok video
    ID actually contains the upload date.

    All we need to do is convert the video ID to binary number that must
    be 64-digits long (prepend enough zeros to make it that long, if necessary).
    After that, we convert the first 32 digits to a decimal number again.
    The resulting number is now an Unix timestamp which is now the upload date
    of video in UTC time.
    """

    binary_num = _convert_decimal_to_binary(video_id)

    # Get the first 32 digits of binary num and then convert it to
    # a decimal number, which results into a Unix timestamp
    unix_timestamp = int(binary_num[:32], 2)

    # Convert the Unix timestamp into a datetime object. Take note that the
    # upload date of all TikTok video IDs are in UTC time
    return datetime.fromtimestamp(unix_timestamp, tz=UTC)


def assign_output_paths(video: "Video") -> None:
    """Assigns the output directory and file path for the Video object.
    If the video has been downloaded already, this will raise an error.
    """

    username = video.username
    video_id = video.video_id
    filename_template = video.filename_template
    date = video.date
    download_dir = _get_download_dir(
        custom_downloads_dir=video.config.get_value(ConfigKey.DOWNLOAD_DIR),
    )

    assert isinstance(video_id, int)

    if username is not None:
        output_path = pathlib.Path(download_dir, username)
        video_filename = _get_video_filename(video_id, username, date, filename_template)
        pathlib.Path(output_path).mkdir(exist_ok=True, parents=True)
        video_file = pathlib.Path(output_path, video_filename)

        if os.path.exists(video_file):
            raise VideoFileAlreadyExistsError(video_filename, username)

        video.output_file_dir = output_path
        video.output_file_path = video_file


def _get_normalized_url(video_link: str, proxy: str | None = None) -> str:
    """Returns a normalized URL whenever the inputted video link doesn't contain the username and the video ID
    (e.g., https://vt.tiktok.com/AbCdEfGhI).

    This is needed so that we can extract the username and the video ID, which are both needed later in the
    program after we have downloaded the video so that we can assign the output file path and name for the video.
    """

    if not video_link.startswith(r"https://") and not video_link.startswith(r"http://"):
        video_link = "https://" + video_link

    if proxy is not None:
        proxies = {"http": proxy, "https": proxy}
    else:
        proxies = None

    response = requests.get(video_link, allow_redirects=True, timeout=30, proxies=proxies)
    return response.url


def _get_download_dir(custom_downloads_dir: str | None) -> pathlib.Path:
    if custom_downloads_dir:
        return pathlib.Path(custom_downloads_dir)
    return DOWNLOAD_PATH


def _convert_decimal_to_binary(number: int) -> str:
    # Gets the binary num excluding the '0b' prefix returned by bin()
    binary_num = f"{number:b}"
    binary_num_len = len(binary_num)

    if binary_num_len == IDEAL_BINARY_NUM_LEN:
        return binary_num

    # If the length of the binary number is less than 64, prepend
    # enough zeros to ensure it is 64 digits long

    zeros_to_prepend = IDEAL_BINARY_NUM_LEN - binary_num_len
    zeros_string = ""

    for _ in range(zeros_to_prepend):
        zeros_string += "0"

    return zeros_string + binary_num


def _get_video_filename(video_id: int, username: str, date: datetime, filename_template: str | None) -> str:
    if filename_template is None:
        return str(video_id) + ".mp4"

    formatted_filename = _format_date(date, filename_template)
    formatted_filename = formatted_filename.replace("{username}", username)
    formatted_filename = formatted_filename.replace("{video_id}", str(video_id))  # noqa: RUF027
    formatted_filename += ".mp4"

    return formatted_filename


def _format_date(date: datetime, filename_template: str) -> str:
    """Returns a filename with formatted date based on the
    given date format provided via `{date:...}` value from `--filename-template`
    arg.
    """

    # Pattern to capture the date placeholder and the date format value
    pattern = r"({date(:(.+?))?})"

    matched_str = re.search(pattern, filename_template)

    if matched_str is None:
        raise InvalidDateFormatError

    date_placeholder = matched_str.group(1)  # i.e., `{date:%Y%m%d_%H%M%S}`
    date_fmt = matched_str.group(3)  # i.e., `%Y%m%d_%H%M%S`

    # User can input `{date}` only from the `--filename-template` arg. If that happens,
    # date_fmt will become None as this don't match with the date_fmt RegEx.
    # To handle this, we will just use a DEFAULT_FORMAT for `formatted_date` if
    # `date_fmt` is None

    if date_fmt is None:
        formatted_date = date.strftime(DEFAULT_DATE_FORMAT)
    else:
        formatted_date = date.strftime(date_fmt)

    return re.sub(date_placeholder, formatted_date, filename_template)
