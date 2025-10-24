from argparse import Namespace
from typing import Any
from tikorgzo.config import mapper
from tikorgzo.config import parser
from tikorgzo.config.model import ConfigKey
from tikorgzo.config.constants import DEFAULT_CONFIG_OPTS


class ConfigProvider:
    """Configuration provider that manages configuration from CLI and config files."""

    def __init__(self) -> None:
        self.config: dict[str, dict | None] = {
            "cli": None,
            "config_file": None
        }

    def get_value(self, key: ConfigKey) -> Any:
        """Get the config value for the given key, prioritizing CLI over config file over default."""

        cli_config = self.config.get("cli")
        config_file_config = self.config.get("config_file")

        cli_value = cli_config[key] if cli_config and key in cli_config else None
        file_value = config_file_config[key] if config_file_config and key in config_file_config else None

        # Prioritize CLI value over config file value and default as last resort
        return cli_value or file_value or DEFAULT_CONFIG_OPTS[key]

    def map_from_cli(self, args: Namespace) -> None:
        """Map argparse Namespace to internal config dict structure."""

        self.config["cli"] = mapper.map_from_cli(args)

    def map_from_config_file(self, config_paths: list[str]) -> None:
        """Map loaded config file dict to internal config dict structure."""

        parsed_config = parser.parse_from_config(config_paths)
        self.config["config_file"] = mapper.map_from_config_file(parsed_config) if parsed_config else None
