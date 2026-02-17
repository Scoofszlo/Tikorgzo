from enum import StrEnum
from pathlib import Path
from typing import Any

from platformdirs import user_data_path, user_documents_path

from tikorgzo.constants import APP_NAME, DIRECT_EXTRACTOR_NAME, TIKWM_EXTRACTOR_NAME

CONFIG_VARIABLES: dict[str, dict[str, Any]] = {
    "extractor": {
        "default": TIKWM_EXTRACTOR_NAME,
        "type": str,
        "allowed_values": [TIKWM_EXTRACTOR_NAME, DIRECT_EXTRACTOR_NAME],
    },
    "download_dir": {
        "default": None,
        "type": str,
    },
    "extraction_delay": {
        "default": 1,
        "type": (float, int),
        "constraints": {
            "min": 0,
            "max": 60,
        },
    },
    "max_concurrent_downloads": {
        "default": 4,
        "type": int,
        "constraints": {
            "min": 1,
            "max": 16,
        },
    },
    "filename_template": {
        "default": None,
        "type": str,
    },
    "lazy_duplicate_check": {
        "default": False,
        "type": bool,
    },
}

DEFAULT_CONFIG_OPTS = {key: value["default"] for key, value in CONFIG_VARIABLES.items()}
CONFIG_FILE_NAME = "tikorgzo.conf"
CONFIG_PATH_LOCATIONS = [
    Path(Path.cwd(), CONFIG_FILE_NAME),
    Path(user_data_path(), APP_NAME, CONFIG_FILE_NAME),
    Path(user_documents_path(), APP_NAME, CONFIG_FILE_NAME),
]


class MapSource(StrEnum):
    CLI = "CLI"
    CONFIG_FILE = "config file"
