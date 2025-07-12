import os
import re
from typing import Optional

import requests

from tikorgzo.constants import DOWNLOAD_PATH
from tikorgzo.exceptions import InvalidVideoLink, VideoFileAlreadyExistsError, VideoIDExtractionError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tikorgzo.core.video_info import VideoInfo
    # If doing this directly, this causes circular import so the alternative is
    # to forward reference the VideoInfo of the _process_output_paths() for
    # type hinting so that we don't need direct import of this class

USERNAME_REGEX = r"\/@([\w\.\-]+)\/video\/\d+"
NORMAL_TIKTOK_VIDEO_LINK_REGEX = r"https?://(www\.)?tiktok\.com/@[\w\.\-]+/video/\d+(\?.*)?$"
VT_TIKTOK_VIDEO_LINK_REGEX = r"https?://vt\.tiktok\.com/"


class VideoInfoProcessor:
    def normalize_video_link(self, video_link: str):
        if re.search(NORMAL_TIKTOK_VIDEO_LINK_REGEX, video_link):
            return video_link

        elif re.search(VT_TIKTOK_VIDEO_LINK_REGEX, video_link):
            video_link = self._get_normalized_url(video_link)
            return video_link

        elif len(video_link) == 19 and video_link.isdigit():
            return video_link

        raise InvalidVideoLink(video_link)

    def _get_normalized_url(self, video_link):
        response = requests.get(video_link, allow_redirects=True)
        return response.url

    def extract_video_id(self, video_link: str) -> int:
        match = re.search(r'/video/(\d+)', video_link)
        if match:
            return int(match.group(1))

        elif len(video_link) == 19 and video_link.isdigit():
            return int(video_link)

        match = re.search(r'/(\d+)_original\.mp4', video_link)
        if match:
            return int(match.group(1))

        raise VideoIDExtractionError()

    def check_if_already_downloaded(self, filename: str):
        """Recursively checks the output folder, which is the default DOWNLOAD_PATH,
        to see if a file (where the filename is a video ID) already exists. If true,
        this will raise an error."""

        filename += ".mp4"

        for root, _, filenames in os.walk(DOWNLOAD_PATH):
            for f in filenames:
                if f == filename:
                    username = os.path.basename(root)
                    raise VideoFileAlreadyExistsError(filename, username)

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

    def _process_output_paths(self, video_info_obj: "VideoInfo") -> None:
        """Determines and creates the output directory and file path for the video.
        If the video has been downloaded already, this will raise an error."""

        username = video_info_obj._username
        video_id = video_info_obj._video_id

        assert isinstance(video_id, int)

        video_filename = str(video_id) + ".mp4"

        if username is not None:
            output_path = os.path.join(DOWNLOAD_PATH, username)
            os.makedirs(output_path, exist_ok=True)
            video_file = os.path.join(output_path, video_filename)

            if os.path.exists(video_file):
                raise VideoFileAlreadyExistsError(video_filename, username)

            video_info_obj._output_file_dir = output_path
            video_info_obj._output_file_path = video_file
