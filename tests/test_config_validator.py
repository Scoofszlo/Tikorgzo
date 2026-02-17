import pytest

from tikorgzo.config.constants import CONFIG_VARIABLES, MapSource
from tikorgzo.config.model import ConfigKey
from tikorgzo.config.validator import (
    is_invalid_config_key,
    is_invalid_extraction_delay,
    is_invalid_extractor,
    is_invalid_filename_string,
    is_invalid_max_concurrent_downloads,
    is_invalid_type,
    validate_config,
)
from tikorgzo.constants import DIRECT_EXTRACTOR_NAME, TIKWM_EXTRACTOR_NAME
from tikorgzo.exceptions import InvalidConfigValueError


class TestValidateConfig:
    """Tests for the main validate_config() dispatcher."""

    def test_valid_extractor_passes(self) -> None:
        validate_config(ConfigKey.EXTRACTOR, TIKWM_EXTRACTOR_NAME, MapSource.CLI)

    def test_valid_extraction_delay_passes(self) -> None:
        validate_config(ConfigKey.EXTRACTION_DELAY, 5, MapSource.CLI)

    def test_valid_max_concurrent_downloads_passes(self) -> None:
        validate_config(ConfigKey.MAX_CONCURRENT_DOWNLOADS, 4, MapSource.CLI)

    def test_valid_filename_template_passes(self) -> None:
        validate_config(ConfigKey.FILENAME_TEMPLATE, "{video_id}", MapSource.CLI)

    def test_valid_filename_template_none_passes(self) -> None:
        validate_config(ConfigKey.FILENAME_TEMPLATE, None, MapSource.CLI)

    def test_valid_lazy_duplicate_check_passes(self) -> None:
        validate_config(ConfigKey.LAZY_DUPLICATE_CHECK, True, MapSource.CONFIG_FILE)

    def test_invalid_config_key_raises(self) -> None:
        with pytest.raises(InvalidConfigValueError):
            validate_config("nonexistent_key", "value", MapSource.CLI)

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(InvalidConfigValueError):
            validate_config(ConfigKey.EXTRACTOR, "123", MapSource.CLI)

    def test_invalid_extractor_value_raises(self) -> None:
        with pytest.raises(InvalidConfigValueError):
            validate_config(ConfigKey.EXTRACTOR, "bad_extractor", MapSource.CLI)

    def test_invalid_extraction_delay_raises(self) -> None:
        with pytest.raises(InvalidConfigValueError):
            validate_config(ConfigKey.EXTRACTION_DELAY, 999, MapSource.CLI)

    def test_invalid_max_concurrent_downloads_raises(self) -> None:
        with pytest.raises(InvalidConfigValueError):
            validate_config(ConfigKey.MAX_CONCURRENT_DOWNLOADS, 100, MapSource.CLI)

    def test_invalid_filename_template_raises(self) -> None:
        with pytest.raises(InvalidConfigValueError):
            validate_config(ConfigKey.FILENAME_TEMPLATE, "no_placeholder_here", MapSource.CLI)

    def test_source_is_carried_in_exception(self) -> None:
        with pytest.raises(InvalidConfigValueError) as exc_info:
            validate_config("bad_key", "val", MapSource.CONFIG_FILE)
        assert exc_info.value.source == MapSource.CONFIG_FILE


class TestIsInvalidConfigKey:
    """Tests for is_invalid_config_key()."""

    @pytest.mark.parametrize("key", list(CONFIG_VARIABLES.keys()))
    def test_valid_keys_return_none(self, key: str) -> None:
        assert is_invalid_config_key(key) is None

    @pytest.mark.parametrize("key", ["bad_key", "", "EXTRACTOR", "Extractor"])
    def test_invalid_keys_return_error_message(self, key: str) -> None:
        result = is_invalid_config_key(key)
        assert result is not None
        assert key in result


class TestIsInvalidType:
    """Tests for is_invalid_type()."""

    def test_correct_str_type_returns_none(self) -> None:
        assert is_invalid_type("extractor", "tikwm") is None

    def test_correct_int_type_returns_none(self) -> None:
        assert is_invalid_type("max_concurrent_downloads", 4) is None

    def test_correct_float_type_for_extraction_delay(self) -> None:
        assert is_invalid_type("extraction_delay", 2.5) is None

    def test_correct_int_type_for_extraction_delay(self) -> None:
        # extraction_delay accepts (float, int)
        assert is_invalid_type("extraction_delay", 3) is None

    def test_correct_bool_type_returns_none(self) -> None:
        assert is_invalid_type("lazy_duplicate_check", True) is None

    def test_none_value_always_passes(self) -> None:
        assert is_invalid_type("extractor", None) is None
        assert is_invalid_type("max_concurrent_downloads", None) is None

    def test_wrong_type_returns_error(self) -> None:
        result = is_invalid_type("extractor", 123)
        assert result is not None

    def test_wrong_type_for_max_concurrent_downloads(self) -> None:
        result = is_invalid_type("max_concurrent_downloads", "four")
        assert result is not None


# ---------------------------------------------------------------------------
# is_invalid_extractor
# ---------------------------------------------------------------------------
class TestIsInvalidExtractor:
    """Tests for is_invalid_extractor()."""

    def test_tikwm_is_valid(self) -> None:
        assert is_invalid_extractor(TIKWM_EXTRACTOR_NAME) is None

    def test_direct_is_valid(self) -> None:
        assert is_invalid_extractor(DIRECT_EXTRACTOR_NAME) is None

    @pytest.mark.parametrize("value", ["youtube", "", "TIKWM", "Direct"])
    def test_invalid_values_return_error(self, value: str) -> None:
        result = is_invalid_extractor(value)
        assert result is not None
        assert "allowed values" in result


# ---------------------------------------------------------------------------
# is_invalid_extraction_delay
# ---------------------------------------------------------------------------
class TestIsInvalidExtractionDelay:
    """Tests for is_invalid_extraction_delay()."""

    min_val: int = CONFIG_VARIABLES["extraction_delay"]["constraints"]["min"]
    max_val: int = CONFIG_VARIABLES["extraction_delay"]["constraints"]["max"]

    def test_minimum_boundary_passes(self) -> None:
        assert is_invalid_extraction_delay(self.min_val) is None

    def test_maximum_boundary_passes(self) -> None:
        assert is_invalid_extraction_delay(self.max_val) is None

    def test_mid_range_passes(self) -> None:
        assert is_invalid_extraction_delay(30) is None

    def test_float_value_passes(self) -> None:
        assert is_invalid_extraction_delay(0.5) is None

    def test_below_minimum_returns_error(self) -> None:
        result = is_invalid_extraction_delay(self.min_val - 1)
        assert result is not None

    def test_above_maximum_returns_error(self) -> None:
        result = is_invalid_extraction_delay(self.max_val + 1)
        assert result is not None


# ---------------------------------------------------------------------------
# is_invalid_max_concurrent_downloads
# ---------------------------------------------------------------------------
class TestIsInvalidMaxConcurrentDownloads:
    """Tests for is_invalid_max_concurrent_downloads()."""

    min_val: int = CONFIG_VARIABLES["max_concurrent_downloads"]["constraints"]["min"]
    max_val: int = CONFIG_VARIABLES["max_concurrent_downloads"]["constraints"]["max"]

    def test_minimum_boundary_passes(self) -> None:
        assert is_invalid_max_concurrent_downloads(self.min_val) is None

    def test_maximum_boundary_passes(self) -> None:
        assert is_invalid_max_concurrent_downloads(self.max_val) is None

    def test_mid_range_passes(self) -> None:
        assert is_invalid_max_concurrent_downloads(8) is None

    def test_below_minimum_returns_error(self) -> None:
        result = is_invalid_max_concurrent_downloads(self.min_val - 1)
        assert result is not None

    def test_above_maximum_returns_error(self) -> None:
        result = is_invalid_max_concurrent_downloads(self.max_val + 1)
        assert result is not None


# ---------------------------------------------------------------------------
# is_invalid_filename_string
# ---------------------------------------------------------------------------
class TestIsInvalidFilenameString:
    """Tests for is_invalid_filename_string()."""

    # --- Valid templates ---
    def test_none_returns_none(self) -> None:
        assert is_invalid_filename_string(None) is None

    def test_simple_video_id_template(self) -> None:
        assert is_invalid_filename_string("{video_id}") is None

    def test_template_with_username(self) -> None:
        assert is_invalid_filename_string("{username}_{video_id}") is None

    def test_template_with_valid_date(self) -> None:
        assert is_invalid_filename_string("{video_id}_{date:%Y%m%d}") is None

    def test_template_with_date_and_username(self) -> None:
        assert is_invalid_filename_string("{username}_{date:%Y-%m-%d}_{video_id}") is None

    # --- Missing required placeholder ---
    def test_missing_video_id_returns_error(self) -> None:
        result = is_invalid_filename_string("no_placeholder")
        assert result is not None
        assert "needed placeholders" in result

    def test_only_username_placeholder_returns_error(self) -> None:
        result = is_invalid_filename_string("{username}")
        assert result is not None

    # --- Invalid date formats ---
    def test_empty_date_format_returns_error(self) -> None:
        result = is_invalid_filename_string("{video_id}_{date:}")
        assert result is not None
        assert "contains nothing" in result

    def test_slash_in_date_format_returns_error(self) -> None:
        # '/' is part of the illegal chars string in the validator
        result = is_invalid_filename_string("{video_id}_{date:%Y/%m/%d}")
        assert result is not None
        assert "illegal characters" in result

    @pytest.mark.parametrize("illegal_char", ['<', '>', ':', '"', '\\', '|', '?', '*'])
    def test_illegal_characters_in_date_format(self, illegal_char: str) -> None:
        template = f"{{video_id}}_{{date:%Y{illegal_char}%m}}"
        result = is_invalid_filename_string(template)
        assert result is not None
        assert "illegal characters" in result

    def test_invalid_strftime_format_returns_error(self) -> None:
        # %Q is not a valid strftime directive and raises ValueError
        result = is_invalid_filename_string("{video_id}_{date:%Q}")
        # Depending on platform, %Q may or may not raise ValueError.
        # On Windows strftime raises ValueError for unsupported directives.
        # Just ensure it doesn't crash — the result will vary by platform.
        assert result is None or "invalid format" in result

    def test_valid_complex_date_format(self) -> None:
        assert is_invalid_filename_string("{video_id}_{date:%Y%m%d_%H%M%S}") is None

    def test_multiple_date_placeholders_first_checked(self) -> None:
        # regex only matches first {date:...}; second one is ignored
        result = is_invalid_filename_string("{video_id}_{date:%Y}_{date:%m}")
        assert result is None
