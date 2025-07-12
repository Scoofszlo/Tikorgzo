import os
from tikorgzo.constants import DOWNLOAD_PATH
from tikorgzo.exceptions import VideoFileAlreadyExistsError


def check_if_already_downloaded(filename: str):
    """Recursively checks the output folder, which is the default DOWNLOAD_PATH,
    to see if a file (where the filename is a video ID) already exists. If true,
    this will raise an error."""

    filename += ".mp4"

    for root, _, filenames in os.walk(DOWNLOAD_PATH):
        for f in filenames:
            if f == filename:
                username = os.path.basename(root)
                raise VideoFileAlreadyExistsError(filename, username)
