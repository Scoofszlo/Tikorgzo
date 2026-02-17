from argparse import Namespace
from pathlib import Path

import pytest

from tikorgzo.config.model import ConfigKey
from tikorgzo.config.provider import ConfigProvider
from tikorgzo.constants import DIRECT_EXTRACTOR_NAME, TIKWM_EXTRACTOR_NAME

# Fixtures
@pytest.fixture
def config_provider() -> ConfigProvider:
    return ConfigProvider()

@pytest.fixture
def sample_cli_config() -> dict:
    """Sample CLI configuration dictionary."""
    return {
        ConfigKey.EXTRACTOR: "direct",
        ConfigKey.DOWNLOAD_DIR: "path/to/downloads",
        ConfigKey.EXTRACTION_DELAY: 5,
        ConfigKey.MAX_CONCURRENT_DOWNLOADS: 2,
        ConfigKey.FILENAME_TEMPLATE: "sample_random_template",
        ConfigKey.LAZY_DUPLICATE_CHECK: True,
    }


@pytest.fixture
def sample_config_file_dict() -> dict:
    """Sample config file dictionary."""
    return {
        ConfigKey.EXTRACTOR: DIRECT_EXTRACTOR_NAME,
        ConfigKey.DOWNLOAD_DIR: "tmp/downloads",
        ConfigKey.EXTRACTION_DELAY: 5,
        ConfigKey.MAX_CONCURRENT_DOWNLOADS: 8,
        ConfigKey.FILENAME_TEMPLATE: "sample_random_template",
        ConfigKey.LAZY_DUPLICATE_CHECK: True,
    }


@pytest.fixture
def sample_cli_args_full() -> Namespace:
    """Sample CLI args with all values provided."""
    return Namespace(
        extractor=DIRECT_EXTRACTOR_NAME,
        download_dir="/tmp/downloads",
        extraction_delay=3,
        max_concurrent_downloads=2,
        filename_template=None,
        lazy_duplicate_check=True,
    )


@pytest.fixture
def sample_cli_args_empty() -> Namespace:
    """Sample CLI args with all None values."""
    return Namespace(
        extractor=None,
        download_dir=None,
        extraction_delay=None,
        max_concurrent_downloads=None,
        filename_template=None,
        lazy_duplicate_check=None,
    )


@pytest.fixture
def sample_toml_valid() -> str:
    """Sample valid TOML config content."""
    return """
[generic]
extractor = "tikwm"
max_concurrent_downloads = 2
extraction_delay = 3
lazy_duplicate_check = true
"""


@pytest.fixture
def sample_toml_minimal() -> str:
    """Sample minimal TOML config with only extractor."""
    return """
[generic]
extractor = "direct"
"""

@pytest.fixture
def sample_toml_invalid_table() -> str:
    """Sample TOML with missing [generic] section."""
    return """[generic_wrong]
key = "value"
"""

@pytest.fixture
def sample_toml_invalid_type() -> str:
    """Sample TOML with invalid type for max_concurrent_downloads."""
    return """[generic]
max_concurrent_downloads = "not_a_number"
"""

@pytest.fixture
def sample_toml_extraction_delay_out_of_range() -> str:
    """Sample TOML with extraction_delay out of valid range."""
    return """[generic]
extraction_delay = 120
"""

@pytest.fixture
def sample_toml_max_concurrent_downloads_out_of_range() -> str:
    """Sample TOML with max_concurrent_downloads out of valid range."""
    return """[generic]
max_concurrent_downloads = 17
"""

# Test value retrieval logic
class TestGetValue:
    """Tests for ConfigProvider.get_value()"""

    def test_returns_default_when_no_config_loaded(self, config_provider: ConfigProvider) -> None:
        """Should fall back to DEFAULT_CONFIG_OPTS when nothing is loaded."""
        assert config_provider.get_value(ConfigKey.EXTRACTOR) == TIKWM_EXTRACTOR_NAME
        assert config_provider.get_value(ConfigKey.EXTRACTION_DELAY) == 1
        assert config_provider.get_value(ConfigKey.MAX_CONCURRENT_DOWNLOADS) == 4
        assert config_provider.get_value(ConfigKey.LAZY_DUPLICATE_CHECK) is False

    def test_returns_cli_value_over_default(self, config_provider: ConfigProvider, sample_cli_config: dict) -> None:
        """CLI-parsed values should override defaults."""
        config_provider.config["cli"] = sample_cli_config

        assert config_provider.get_value(ConfigKey.EXTRACTOR) == DIRECT_EXTRACTOR_NAME
        assert config_provider.get_value(ConfigKey.EXTRACTION_DELAY) == 5
        assert config_provider.get_value(ConfigKey.MAX_CONCURRENT_DOWNLOADS) == 2
        assert config_provider.get_value(ConfigKey.FILENAME_TEMPLATE) == "sample_random_template"
        assert config_provider.get_value(ConfigKey.LAZY_DUPLICATE_CHECK) is True

    def test_returns_config_file_value_over_default(self, config_provider: ConfigProvider, sample_config_file_dict: dict) -> None:
        """Config-file-parsed values should override defaults."""
        config_provider.config["config_file"] = sample_config_file_dict

        assert config_provider.get_value(ConfigKey.EXTRACTOR) == DIRECT_EXTRACTOR_NAME
        assert config_provider.get_value(ConfigKey.DOWNLOAD_DIR) == "tmp/downloads"
        assert config_provider.get_value(ConfigKey.EXTRACTION_DELAY) == 5
        assert config_provider.get_value(ConfigKey.MAX_CONCURRENT_DOWNLOADS) == 8
        assert config_provider.get_value(ConfigKey.FILENAME_TEMPLATE) == "sample_random_template"
        assert config_provider.get_value(ConfigKey.LAZY_DUPLICATE_CHECK) is True

    def test_cli_takes_priority_over_config_file(self, config_provider: ConfigProvider) -> None:
        """CLI values should beat config file values."""
        config_provider.config["cli"] = {
            ConfigKey.EXTRACTOR: "direct",
            ConfigKey.EXTRACTION_DELAY: 8,
        }
        config_provider.config["config_file"] = {
            ConfigKey.EXTRACTOR: TIKWM_EXTRACTOR_NAME,
            ConfigKey.EXTRACTION_DELAY: 30,
        }

        assert config_provider.get_value(ConfigKey.EXTRACTION_DELAY) == 8

# Test mapping logic for CLI and config file
class TestMapFromCli:
    """Tests for ConfigProvider.map_from_cli()"""

    def test_maps_cli_args_to_config(self, config_provider: ConfigProvider, sample_cli_args_full: Namespace) -> None:
        """Provided CLI args should be mapped into config['cli']."""
        config_provider.map_from_cli(sample_cli_args_full)

        assert config_provider.config["cli"] is not None

        cli_config = config_provider.config["cli"]

        assert cli_config["extractor"] == DIRECT_EXTRACTOR_NAME
        assert cli_config["download_dir"] == "/tmp/downloads"
        assert cli_config["extraction_delay"] == 3
        assert cli_config["max_concurrent_downloads"] == 2
        assert cli_config["lazy_duplicate_check"] is True

    def test_uses_defaults_for_missing_cli_args(self, config_provider: ConfigProvider, sample_cli_args_empty: Namespace) -> None:
        """Args not provided (None) should fall back to the config default."""
        config_provider.map_from_cli(sample_cli_args_empty)

        assert config_provider.config["cli"] is not None

        assert config_provider.get_value(ConfigKey.EXTRACTOR) == TIKWM_EXTRACTOR_NAME
        assert config_provider.get_value(ConfigKey.EXTRACTION_DELAY) == 1
        assert config_provider.get_value(ConfigKey.MAX_CONCURRENT_DOWNLOADS) == 4
        assert config_provider.get_value(ConfigKey.LAZY_DUPLICATE_CHECK) is False

    def test_partial_cli_args(self, config_provider: ConfigProvider) -> None:
        """Only some args provided — others should get defaults."""
        args = Namespace(
            extractor=DIRECT_EXTRACTOR_NAME,
            download_dir=None,
            extraction_delay=None,
            max_concurrent_downloads=8,
            filename_template=None,
            lazy_duplicate_check=None,
        )

        config_provider.map_from_cli(args)

        assert config_provider.get_value(ConfigKey.EXTRACTOR) == DIRECT_EXTRACTOR_NAME
        assert config_provider.get_value(ConfigKey.MAX_CONCURRENT_DOWNLOADS) == 8
        assert config_provider.get_value(ConfigKey.EXTRACTION_DELAY) == 1

class TestMapFromConfigFile:
    """Tests for ConfigProvider.map_from_config_file()"""

    def _write_toml(self, tmp_path: Path, content: str) -> list[Path]:
        config_file = tmp_path / "tikorgzo.conf"
        config_file.write_text(content, encoding="utf-8")
        return [config_file]

    def test_maps_valid_config_file(self, config_provider: ConfigProvider, tmp_path: Path, sample_toml_valid: str) -> None:
        """A valid config file should populate config['config_file']."""
        paths = self._write_toml(tmp_path, sample_toml_valid)

        config_provider.map_from_config_file(paths)
        assert config_provider.config["config_file"] is not None

        file_config = config_provider.config["config_file"]

        assert file_config["extractor"] == TIKWM_EXTRACTOR_NAME
        assert file_config["max_concurrent_downloads"] == 2
        assert file_config["extraction_delay"] == 3
        assert file_config["lazy_duplicate_check"] is True

    def test_missing_generic_section_yields_none(self, config_provider: ConfigProvider, tmp_path: Path, sample_toml_invalid_table: str) -> None:
        """Config file without [generic] should result in config_file being None."""
        paths = self._write_toml(tmp_path, sample_toml_invalid_table)

        config_provider.map_from_config_file(paths)

        assert config_provider.config["config_file"] is None

    def test_nonexistent_config_file_yields_none(self, config_provider: ConfigProvider) -> None:
        """If no config file exists at any path, config_file should be None."""
        config_provider.map_from_config_file([Path("/nonexistent/tikorgzo.conf")])

        assert config_provider.config["config_file"] is None

    def test_keys_not_in_file_get_defaults(self, config_provider: ConfigProvider, tmp_path: Path, sample_toml_minimal: str) -> None:
        """Keys absent from the config file should fall back to their defaults."""
        paths = self._write_toml(tmp_path, sample_toml_minimal)

        config_provider.map_from_config_file(paths)

        assert config_provider.config["config_file"] is not None
        assert config_provider.get_value(ConfigKey.EXTRACTOR) == DIRECT_EXTRACTOR_NAME
        assert config_provider.get_value(ConfigKey.MAX_CONCURRENT_DOWNLOADS) == 4  # default
        assert config_provider.get_value(ConfigKey.EXTRACTION_DELAY) == 1  # default
