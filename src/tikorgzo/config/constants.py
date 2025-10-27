import os
from typing import Any, Dict

from platformdirs import user_data_path, user_documents_path
from tikorgzo.constants import APP_NAME

CONFIG_VARIABLES: Dict[str, Dict[str, Any]] = {
    "download_dir": {
        "default": None,
        "type": str,
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
    }
}

DEFAULT_CONFIG_OPTS = {key: value["default"] for key, value in CONFIG_VARIABLES.items()}
CONFIG_FILE_NAME = "tikorgzo.conf"
CONFIG_PATH_LOCATIONS = [
    os.path.join(os.getcwd(), CONFIG_FILE_NAME),
    os.path.join(user_data_path(), APP_NAME, CONFIG_FILE_NAME),
    os.path.join(user_documents_path(), APP_NAME, CONFIG_FILE_NAME),
]
