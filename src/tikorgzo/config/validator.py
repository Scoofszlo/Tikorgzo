import re
from datetime import UTC, datetime

from tikorgzo.config.constants import CONFIG_VARIABLES, MapSource
from tikorgzo.config.model import ConfigKey
from tikorgzo.exceptions import InvalidConfigValueError


def validate_config(
        config_key: str,
        value: str | float | bool | None,
        source: MapSource) -> None:
    """Validates config values to ensure that all are properly set."""

    error_msg: str | None = None

    error_msg = is_invalid_config_key(config_key)
    error_msg = error_msg or is_invalid_type(config_key, value)

    if error_msg is not None:
        raise InvalidConfigValueError(error_msg, source)

    if config_key == ConfigKey.EXTRACTOR:
        assert isinstance(value, str)
        error_msg = is_invalid_extractor(value)
    elif config_key == ConfigKey.EXTRACTION_DELAY:
        assert isinstance(value, (int, float))
        error_msg = is_invalid_extraction_delay(value)
    elif config_key == ConfigKey.MAX_CONCURRENT_DOWNLOADS:
        assert isinstance(value, int)
        error_msg = is_invalid_max_concurrent_downloads(value)
    elif config_key == ConfigKey.FILENAME_TEMPLATE:
        assert isinstance(value, str) or value is None
        error_msg = is_invalid_filename_string(value)

    if error_msg is not None:
        raise InvalidConfigValueError(error_msg, source)


def is_invalid_config_key(config_key: str) -> str | None:
    if config_key not in CONFIG_VARIABLES:
        return f"Key '[blue]{config_key}[/blue]' isn't a valid config key."

    return None


def is_invalid_type(config_key: str, value: str | float | bool | None) -> str | None:
    expected_type = CONFIG_VARIABLES[config_key]["type"]

    if value is not None and not isinstance(value, expected_type):
        return f"Key '[blue]{config_key}[/blue]' expects type [green]'{expected_type.__name__}[/green]', got '[yellow]{type(value).__name__}[/yellow]'."

    return None


def is_invalid_extractor(value: str) -> str | None:
    allowed_values = CONFIG_VARIABLES["extractor"]["allowed_values"]

    if value not in allowed_values:
        return f"[blue]'extractor'[/blue] must be one of the allowed values: {allowed_values}."

    return None


def is_invalid_extraction_delay(value: float) -> str | None:
    max_val = CONFIG_VARIABLES["extraction_delay"]["constraints"]["max"]
    min_val = CONFIG_VARIABLES["extraction_delay"]["constraints"]["min"]

    if value is not None and not min_val <= value <= max_val:
        return f"[blue]'extraction_delay'[/blue] must be greater than [green]{min_val}[/green] but less than or equal to [green]{max_val}[/green] seconds."

    return None


def is_invalid_max_concurrent_downloads(value: int) -> str | None:
    max_val = CONFIG_VARIABLES["max_concurrent_downloads"]["constraints"]["max"]
    min_val = CONFIG_VARIABLES["max_concurrent_downloads"]["constraints"]["min"]

    if value is not None and (value > max_val or value < min_val):
        return f"[blue]'max_concurrent_downloads'[/blue] must be in the range of [green]{min_val} to {max_val}[/green]."

    return None


def is_invalid_filename_string(value: str | None) -> str | None:
    """If user uses `--filename-template` arg, this function checks if one of the necessary
    placeholders is included. We iterate through the necessary placeholders
    to check that arg (currently, there is only one required placeholder, but the loop
    allows for easy extension if more are added in the future.).
    """

    if value is None:
        return None

    placeholders = {
        "necessary": ["{video_id}"],
        "optional": ["{username}", r"({date:(.*?)})"],
        # Do not use `r"{date:(.+?)}` as this accidentally spans across the filename_template
        # string and might cause issues with how file is named. `*?` in this date regex ensures
        # that it only captures the value inside the {date:...} and not outside of it
    }

    for placeholder in placeholders["necessary"]:
        if placeholder not in value:
            return f"'[blue]--filename-template[/blue]' does not contain one of the needed placeholders: [green]{placeholders['necessary']}[/green]'."

    # Check if there is a `{date:...}` placeholder
    matched_date = re.search(placeholders["optional"][1], value)
    if matched_date:
        date_fmt = matched_date.group(2)

        if not date_fmt:
            return f"'[blue]--filename-template[/blue]' contains nothing in your '[green]{{date:{date_fmt}}}[/green]' placeholder."

        # Check for illegal filename characters (Windows and Linux)
        illegal_chars = r'<>:"/\\|?*\0'
        if any(char in date_fmt for char in illegal_chars):
            return (
                f"'[blue]--filename-template[/blue]' contains illegal characters in your "
                f"'[green]{{date:{date_fmt}}}[/green]' placeholder. Avoid using any of these "
                f"[yellow]{illegal_chars}[/yellow] on it."
            )

        # Print an error and exit the program when user tries to use a format that doesn't work
        # with `strftime()`
        try:
            datetime.now(tz=UTC).strftime(date_fmt)
        except ValueError:
            return f"'[blue]--filename-template[/blue]' contains invalid format in your '[green]{{date:{date_fmt}}}[/green]' placeholder. Please check again for typos."

    return None
