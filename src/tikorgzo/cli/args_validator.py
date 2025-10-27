from argparse import Namespace
from datetime import datetime
import re
import sys

from tikorgzo.console import console
from tikorgzo.cli.args_handler import ArgsHandler

ah: ArgsHandler
args: Namespace


def validate_args(ah_param: ArgsHandler, args_param: Namespace) -> None:
    """Validates args entered to ensure that all are properly set."""
    global ah, args
    ah = ah_param
    args = args_param

    _show_cli_help()
    _raise_error_if_invalid_max_concurrent_downloads()
    _raise_error_if_invalid_filename_string()


def _show_cli_help() -> None:
    if not args.file and not args.link:
        ah._parser.print_help()
        exit(0)


def _raise_error_if_invalid_max_concurrent_downloads() -> None:
    if args.max_concurrent_downloads:
        if args.max_concurrent_downloads > 16 or args.max_concurrent_downloads < 1:
            console.print("[red]error[/red]: '[blue]--max-concurrent-downloads[/blue]' must be in the range of 1 to 16.")
            sys.exit(1)


def _raise_error_if_invalid_filename_string() -> None:
    """If user uses `--filename-template` arg, this function checks if one of the necessary
    placeholders is included. We iterate through the necessary placeholders
    to check that arg (currently, there is only one required placeholder, but the loop
    allows for easy extension if more are added in the future.)"""

    placeholders = {
        "necessary": ["{video_id}"],
        "optional": ["{username}", r"({date:(.*?)})"]
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

        if date_fmt == "":
            console.print(f"[red]error[/red]: '[blue]--filename-template[/blue]' contains nothing in your '[green]{{date:{date_fmt}}}[/green]' placeholder.")
            sys.exit(1)

        # Check for illegal filename characters (Windows and Linux)
        illegal_chars = r'<>:"/\\|?*\0'
        if any(char in date_fmt for char in illegal_chars):
            console.print(
                f"[red]error[/red]: '[blue]--filename-template[/blue]' contains illegal characters in your "
                f"'[green]{{date:{date_fmt}}}[/green]' placeholder. Avoid using any of these "
                f"[yellow]{illegal_chars}[/yellow] on it."
            )
            sys.exit(1)

        # Print an error and exit the program when user tries to use a format that doesn't work
        # with `strftime()`
        try:
            datetime.now().strftime(date_fmt)
        except ValueError:
            console.print(f"[red]error[/red]: '[blue]--filename-template[/blue]' contains invalid format in your '[green]{{date:{date_fmt}}}[/green]' placeholder. Please check again for typos.")
            sys.exit(1)
