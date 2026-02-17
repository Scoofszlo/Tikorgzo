from argparse import Namespace
from typing import Any

from tikorgzo.config.constants import CONFIG_VARIABLES, MapSource
from tikorgzo.config.validator import validate_config
from tikorgzo.console import console


def map_from_cli(args: Namespace) -> dict[str, Any]:
    """Map argparse Namespace to internal config dict structure."""

    config: dict[str, Any] = {}

    for config_key in CONFIG_VARIABLES:
        # Use getattr to safely get attribute from Namespace
        value = getattr(args, config_key, None)

        if value is not None:
            validate_config(config_key, value, MapSource.CLI)
            config[config_key] = value
        else:
            config[config_key] = None

    return config


def map_from_config_file(loaded_config: dict[str, Any]) -> dict[str, Any] | None:
    """Map loaded config file dict to internal config dict structure."""

    try:
        loaded_config = loaded_config["generic"]
    except KeyError:
        # We don't stop the program here since config keys aren't loaded anyway,
        # and is not likely for the program to behave unexpectedly.
        console.print("[yellow]warning[/yellow]: '[blue]generic[/blue]' section not found in config file. Skipping config file usage...")
        return None

    config: dict[str, Any] = {}

    for key in loaded_config:
        validate_config(key, loaded_config[key], MapSource.CONFIG_FILE)
        config[key] = loaded_config[key]

    return config
