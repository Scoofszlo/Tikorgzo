from argparse import Namespace
import sys
from typing import Optional
from tikorgzo.config.model import ConfigKey
from tikorgzo.console import console
from tikorgzo.config.constants import CONFIG_VARIABLES


def map_from_cli(args: Namespace) -> dict:
    """Map argparse Namespace to internal config dict structure."""

    config = {}

    for config_key in CONFIG_VARIABLES:
        # Use getattr to safely get attribute from Namespace
        value = getattr(args, config_key, None)

        if value is not None:
            config[config_key] = value
        else:
            config[config_key] = None

    return config


def map_from_config_file(loaded_config: dict) -> Optional[dict]:
    """Map loaded config file dict to internal config dict structure."""

    try:
        loaded_config = loaded_config["generic"]
    except KeyError:
        # We don't stop the program here since config keys aren't loaded anyway,
        # and is not likely for the program to behave unexpectedly.
        console.print("[yellow]warning[/yellow]: '[blue]generic[/blue]' section not found in config file. Skipping config file usage...")
        return None

    config = {}

    for key in loaded_config:
        if key not in CONFIG_VARIABLES:
            console.print(f"[red]error[/red]: Key '[blue]{key}[/blue]' from config file isn't a valid config key.")
            sys.exit(1)

        expected_type = CONFIG_VARIABLES[key]["type"]
        value = loaded_config[key]

        if value is not None and not isinstance(value, expected_type):
            # Program must be stopped here as loading incompatible types (which obviously has different data) can
            # lead to unexpected behavior.
            console.print(f"[red]error[/red]: Key '[blue]{key}[/blue]' from config file expects type [green]'{expected_type.__name__}[/green]', got '[yellow]{type(value).__name__}[/yellow]'.")
            sys.exit(1)

        if key == ConfigKey.MAX_CONCURRENT_DOWNLOADS:
            constraints = CONFIG_VARIABLES[key]["constraints"]
            min_value = constraints["min"]
            max_value = constraints["max"]

            if value > max_value or value < min_value:
                console.print(f"[red]error[/red]: Key '[blue]{key}[/blue]' from config file must be in the range of 1 to 16.")
                sys.exit(1)

        config[key] = loaded_config[key]

    return config
