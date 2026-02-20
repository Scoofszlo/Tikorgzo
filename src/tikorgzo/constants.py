from enum import Enum, auto
from pathlib import Path

from platformdirs import user_data_path, user_downloads_path

# Program-wide constants
APP_NAME = "Tikorgzo"
DOWNLOAD_PATH = Path(user_downloads_path()) / APP_NAME
CHROME_USER_DATA_DIR = Path(user_data_path()) / APP_NAME / "chrome_user_data"
DEFAULT_DATE_FORMAT = r"%Y%m%d_%H%M%S"

# TikTok constants
TIKTOK_ID_LENGTH = 19

# Extractor related constants
TIKWM_EXTRACTOR_NAME = "tikwm"
DIRECT_EXTRACTOR_NAME = "direct"


STATUS_OK = 200


class DownloadStatus(Enum):
    UNSTARTED = auto()
    QUEUED = auto()
    INTERRUPTED = auto()
    COMPLETED = auto()
