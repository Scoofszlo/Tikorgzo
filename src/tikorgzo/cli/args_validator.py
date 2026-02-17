import re
import sys
from argparse import Namespace
from datetime import UTC, datetime

from tikorgzo.cli.args_handler import ArgsHandler
from tikorgzo.config.constants import CONFIG_VARIABLES
from tikorgzo.console import console


def validate_args(ah: ArgsHandler, args: Namespace) -> None:
    """Validates args entered to ensure that all are properly set."""
    _raise_error_if_invalid_extractor(args)
    _raise_error_if_invalid_extraction_delay(args)
    _raise_error_if_invalid_max_concurrent_downloads(args)
    _raise_error_if_invalid_filename_string(args)


def _raise_error_if_invalid_extractor(args: Namespace) -> None:
    if args.extractor is not None:
        allowed_values = CONFIG_VARIABLES["extractor"]["allowed_values"]

        if args.extractor not in allowed_values:
            console.print(f"[red]error[/red]: '[blue]--extractor[/blue]' must be one of the allowed values: {allowed_values}.")
            sys.exit(1)


def _raise_error_if_invalid_extraction_delay(args: Namespace) -> None:
    max_val = CONFIG_VARIABLES["extraction_delay"]["constraints"]["max"]
    min_val = CONFIG_VARIABLES["extraction_delay"]["constraints"]["min"]

    if args.extraction_delay is not None and min_val < args.extraction_delay > max_val:
        console.print("[red]error[/red]: '[blue]--extraction-delay[/blue]' must be greater than 0 but less than or equal to 60 seconds.")
        sys.exit(1)


def _raise_error_if_invalid_max_concurrent_downloads(args: Namespace) -> None:
    max_val = CONFIG_VARIABLES["max_concurrent_downloads"]["constraints"]["max"]
    min_val = CONFIG_VARIABLES["max_concurrent_downloads"]["constraints"]["min"]

    if args.max_concurrent_downloads is not None and (args.max_concurrent_downloads > max_val or args.max_concurrent_downloads < min_val):
        console.print(f"[red]error[/red]: '[blue]--max-concurrent-downloads[/blue]' must be in the range of {min_val} to {max_val}.")
        sys.exit(1)


def _raise_error_if_invalid_filename_string(args: Namespace) -> None:
    """If user uses `--filename-template` arg, this function checks if one of the necessary
    placeholders is included. We iterate through the necessary placeholders
    to check that arg (currently, there is only one required placeholder, but the loop
    allows for easy extension if more are added in the future.).
    """

    placeholders = {
        "necessary": ["{video_id}"],
        "optional": ["{username}", r"({date:(.*?)})"],
        # Do not use `r"{date:(.+?)}` as this accidentally spans across the filename_template
        # string and might cause issues with how file is named. `*?` in this date regex ensures
        # that it only captures the value inside the {date:...} and not outside of it
    }

    for placeholder in placeholders["necessary"]:
        if args.filename_template is None:
            return

        if placeholder not in args.filename_template:
            console.print(f"[red]error[/red]: '[blue]--filename-template[/blue]' does not contain one of the needed placeholders: [green]{placeholders['necessary']}[/green]")
            sys.exit(1)

    # Check if there is a `{date:...}` placeholder
    matched_date = re.search(placeholders["optional"][1], args.filename_template)
    if matched_date:
        date_fmt = matched_date.group(2)

        if not date_fmt:
            console.print(f"[red]error[/red]: '[blue]--filename-template[/blue]' contains nothing in your '[green]{{date:{date_fmt}}}[/green]' placeholder.")
            sys.exit(1)

        # Check for illegal filename characters (Windows and Linux)
        illegal_chars = r'<>:"/\\|?*\0'
        if any(char in date_fmt for char in illegal_chars):
            console.print(
                f"[red]error[/red]: '[blue]--filename-template[/blue]' contains illegal characters in your "
                f"'[green]{{date:{date_fmt}}}[/green]' placeholder. Avoid using any of these "
                f"[yellow]{illegal_chars}[/yellow] on it.",
            )
            sys.exit(1)

        # Print an error and exit the program when user tries to use a format that doesn't work
        # with `strftime()`
        try:
            datetime.now(tz=UTC).strftime(date_fmt)
        except ValueError:
            console.print(f"[red]error[/red]: '[blue]--filename-template[/blue]' contains invalid format in your '[green]{{date:{date_fmt}}}[/green]' placeholder. Please check again for typos.")
            sys.exit(1)
