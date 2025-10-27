import os
import re
import requests
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from tikorgzo.config.model import ConfigKey
from tikorgzo.constants import DOWNLOAD_PATH
from tikorgzo.exceptions import InvalidDateFormat, InvalidVideoLink, VideoFileAlreadyExistsError, VideoIDExtractionError

if TYPE_CHECKING:
    from tikorgzo.core.video.model import Video
    # If doing this directly, this causes circular import so the alternative is
    # to forward reference the VideoInfo of the _process_output_paths() for
    # type hinting so that we don't need direct import of this class

USERNAME_REGEX = r"\/@([\w\.\-]+)\/video\/\d+"
NORMAL_TIKTOK_VIDEO_LINK_REGEX = r"(https?://)?(www\.)?tiktok\.com/@[\w\.\-]+/video/\d+(\?.*)?$"
VT_TIKTOK_VIDEO_LINK_REGEX = r"(https?://)?vt\.tiktok\.com/"


class VideoInfoProcessor:
    def validate_video_link(self, video_link: str) -> str:
        """Checks if the video link is a valid TikTok video link or a valid video ID."""

        if re.search(NORMAL_TIKTOK_VIDEO_LINK_REGEX, video_link):
            return video_link

        elif re.search(VT_TIKTOK_VIDEO_LINK_REGEX, video_link):
            video_link = self._get_normalized_url(video_link)
            return video_link

        elif len(video_link) == 19 and video_link.isdigit():
            return video_link

        raise InvalidVideoLink(video_link)

    def extract_video_id(self, video_link: str) -> int:
        """Extracts the video ID which is a 19-digit long that uniquely identifies a TikTok video."""
        match = re.search(r'/video/(\d+)', video_link)
        if match:
            return int(match.group(1))

        elif len(video_link) == 19 and video_link.isdigit():
            return int(video_link)

        match = re.search(r'/(\d+)_original\.mp4', video_link)
        if match:
            return int(match.group(1))

        raise VideoIDExtractionError()

    def check_if_already_downloaded(
            self,
            video_id: int,
            lazy_duplicate_check: bool,
            custom_download_dir: Optional[str] = None,
    ) -> None:
        """Recursively checks the output folder, which is the default DOWNLOAD_PATH,
        to see if a file already exists whether the filename contains the video ID or not.
        If true, this will raise an error.

        This function only runs when `--strict-duplicate-check` is enabled.
        """

        if lazy_duplicate_check is True:
            return

        download_dir = self._get_download_dir(custom_download_dir)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)

        for root, _, filenames in os.walk(download_dir):
            for f in filenames:
                if str(video_id) in f:
                    username = os.path.basename(root)
                    raise VideoFileAlreadyExistsError(f, username)

    def get_date(self, video_id: int) -> datetime:
        """Gets the date from the video ID.

        This one is pretty interesting as I read from this article
        (https://dfir.blog/tinkering-with-tiktok-timestamps/) that TikTok video
        ID actually contains the upload date.

        All we need to do is convert the video ID to binary number that must
        be 64-digits long (prepend enough zeros to make it that long, if necessary).
        After that, we convert the first 32 digits to a decimal number again.
        The resulting number is now an Unix timestamp which is now the upload date
        of video in UTC time."""

        binary_num = self._convert_decimal_to_binary(video_id)

        # Get the first 32 digits of binary num and then convert it to
        # a decimal number, which results into a Unix timestamp
        unix_timestamp = int(binary_num[:32], 2)

        # Convert the Unix timestamp into a datetime object. Take note that the
        # upload date of all TikTok video IDs are in UTC time
        dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)

        return dt

    def process_output_paths(self, video: "Video") -> None:
        """Determines and creates the output directory and file path for the video.
        If the video has been downloaded already, this will raise an error."""

        username = video._username
        video_id = video._video_id
        filename_template = video._filename_template
        date = video._date
        download_dir = self._get_download_dir(
            custom_downloads_dir=video._config.get_value(ConfigKey.DOWNLOAD_DIR)
        )

        assert isinstance(video_id, int)

        if username is not None:
            output_path = os.path.join(download_dir, username)
            video_filename = self._get_video_filename(video_id, username, date, filename_template)
            os.makedirs(output_path, exist_ok=True)
            video_file = os.path.join(output_path, video_filename)

            if os.path.exists(video_file):
                raise VideoFileAlreadyExistsError(video_filename, username)

            video._output_file_dir = output_path
            video._output_file_path = video_file

    def _get_normalized_url(self, video_link: str) -> str:
        """Returns a normalized URL whenever the inputted video link doesn't contain the username and the video ID
        (e.g., https://vt.tiktok.com/AbCdEfGhI).

        This is needed so that we can extract the username and the video ID when the normalized URL is extracted, which
        are both needed so that when we have downloaded the video, they will be saved in the Downloads folder in which they
        are grouped by username and the filename will be the video ID."""

        if not video_link.startswith(r"https://") and not video_link.startswith(r"http://"):
            video_link = "https://" + video_link

        response = requests.get(video_link, allow_redirects=True)
        return response.url

    def _process_username(self, video_link: str) -> Optional[str]:
        """Some video links include username so this method processes those links
        and extracts the username from it.

        If nothing can be extracted, this returns None
        """
        match = re.search(USERNAME_REGEX, video_link)

        if match:
            return match.group(1)
        else:
            return None

    def _get_video_filename(self, video_id: int, username: str, date: datetime, filename_template: Optional[str]) -> str:
        if filename_template is None:
            return str(video_id) + ".mp4"

        formatted_filename = self._format_date(date, filename_template)
        formatted_filename = formatted_filename.replace("{username}", username)
        formatted_filename = formatted_filename.replace("{video_id}", str(video_id))
        formatted_filename += ".mp4"

        return formatted_filename

    def _convert_decimal_to_binary(self, number: int) -> str:
        # Gets the binary num excluding the '0b' prefix returned by bin()
        binary_num = bin(number)[2:]
        binary_num_len = len(binary_num)

        if binary_num_len == 64:
            return binary_num

        # If the length of the binary number is less than 64, prepend
        # enough zeros to ensure it is 64 digits long

        zeros_to_prepend = 64 - binary_num_len
        zeros_string = ""

        for _ in range(zeros_to_prepend):
            zeros_string += "0"

        new_binary_num = zeros_string + binary_num

        return new_binary_num

    def _format_date(self, date: datetime, filename_template: str) -> str:
        """Returns a filename with formatted date based on the
        given date format provided via `{date:...}` value from `--filename-template`
        arg"""

        # Pattern to capture the date placeholder and the date format value
        pattern = r"({date(:(.+?))?})"

        matched_str = re.search(pattern, filename_template)

        if matched_str is None:
            raise InvalidDateFormat()

        date_placeholder = matched_str.group(1)  # i.e., `{date:%Y%m%d_%H%M%S}`
        date_fmt = matched_str.group(3)  # i.e., `%Y%m%d_%H%M%S`

        # User can input `{date}` only from the `--filename-template` arg. If that happens,
        # date_fmt will become None as this don't match with the date_fmt RegEx.
        # To handle this, we will just use a DEFAULT_FORMAT for `formatted_date` if
        # `date_fmt` is None

        if date_fmt is None:
            DEFAULT_FORMAT = r"%Y%m%d_%H%M%S"
            formatted_date = date.strftime(DEFAULT_FORMAT)
        else:
            formatted_date = date.strftime(date_fmt)

        formatted_filename = re.sub(date_placeholder, formatted_date, filename_template)

        return formatted_filename

    def _get_download_dir(self, custom_downloads_dir: Optional[str]) -> str:
        if custom_downloads_dir:
            return custom_downloads_dir
        return DOWNLOAD_PATH
