from enum import Enum, auto
from platformdirs import user_data_path, user_downloads_path
import os

APP_NAME = "Tikorgzo"
DOWNLOAD_PATH = os.path.join(user_downloads_path(), APP_NAME)
CHROME_USER_DATA_DIR = os.path.join(user_data_path(), APP_NAME, "chrome_user_data")


class DownloadStatus(Enum):
    UNSTARTED = auto()
    QUEUED = auto()
    INTERRUPTED = auto()
    COMPLETED = auto()
