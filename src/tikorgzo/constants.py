from enum import Enum, auto
from platformdirs import user_downloads_path
import os

APP_NAME = "Tikorgzo"
DOWNLOAD_PATH = os.path.join(user_downloads_path(), APP_NAME)


class DownloadStatus(Enum):
    UNSTARTED = auto()
    QUEUED = auto()
    INTERRUPTED = auto()
    COMPLETED = auto()
