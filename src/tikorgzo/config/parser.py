import os
import pathlib
import sys
from pathlib import Path
from typing import Any

import toml

from tikorgzo.console import console


def parse_from_config(config_path_list: list[Path]) -> dict[str, Any] | None:
    """Parse configuration from config file if exists."""

    for config_path in config_path_list:
        if os.path.exists(config_path):
            try:
                with pathlib.Path(config_path).open("r", encoding="utf-8") as f:
                    return toml.load(f)
            except toml.TomlDecodeError as e:
                console.print(f"[yellow]error[/yellow]: Failed to parse TOML from '{config_path}' due to '[blue]{e.msg} (line {e.lineno} column {e.colno} char {e.pos})[/blue]'.")
                sys.exit(1)

    return None
