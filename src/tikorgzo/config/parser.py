import os
import pathlib
from pathlib import Path
from typing import Any

import toml

from tikorgzo.exceptions import InvalidConfigFileStructureError


def parse_from_config(config_path_list: list[Path]) -> dict[str, Any] | None:
    """Parse configuration from config file if exists."""

    for config_path in config_path_list:
        if os.path.exists(config_path):
            try:
                with pathlib.Path(config_path).open("r", encoding="utf-8") as f:
                    return toml.load(f)
            except toml.TomlDecodeError as e:
                raise InvalidConfigFileStructureError(config_path, e) from e

    return None
