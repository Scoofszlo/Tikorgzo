from argparse import Namespace
import sys

from tikorgzo.console import console
from tikorgzo.cli.args_handler import ArgsHandler

ah: ArgsHandler
args: Namespace


def validate_args(ah_param: ArgsHandler, args_param: Namespace):
    """Validates args entered to ensure that all are properly set."""
    global ah, args
    ah = ah_param
    args = args_param

    _show_cli_help()
    _raise_error_if_invalid_max_concurrent_downloads()
    _raise_error_if_invalid_filename_string()


def _show_cli_help():
    if not args.file and not args.link:
        ah._parser.print_help()
        exit(0)


def _raise_error_if_invalid_max_concurrent_downloads():
    if args.max_concurrent_downloads:
        if args.max_concurrent_downloads > 16 or args.max_concurrent_downloads < 1:
            console.print("[red]error[/red]: '[blue]--max-concurrent-downloads[/blue]' must be in the range of 1 to 16.")
            sys.exit(1)


def _raise_error_if_invalid_filename_string():
    placeholders = {
        "necessary": ["video_id"],
        "optional": ["username"]
    }

    for placeholder in placeholders["necessary"]:
        if placeholder not in args.filename_template:
            console.print(f"[red]error[/red]: '[blue]--filename-template[/blue]' does not contain one of the needed placeholders: [green]{placeholders['necessary']}[/green]")
            sys.exit(1)
