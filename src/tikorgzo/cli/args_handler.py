import argparse
from rich_argparse import RichHelpFormatter

from tikorgzo.utils import display_version


class ArgsHandler:
    def __init__(self) -> None:
        self._parser: argparse.ArgumentParser = argparse.ArgumentParser(
            description="Tikorgzo - A TikTok video downloader that downloads source quality video.",
            formatter_class=RichHelpFormatter
        )
        self._init_args()

    def parse_args(self) -> argparse.Namespace:
        args = self._parser.parse_args()
        return args

    def _init_args(self) -> None:
        self._parser.add_argument(
            "-l", "--link",
            nargs="+",
            help="The link to download (can be multiple links)",
        )
        self._parser.add_argument(
            "-f", "--file",
            help="A text file containing links"
        )
        self._parser.add_argument(
            "--download-dir",
            help="Set the download directory (default: Downloads folder)",
            type=str,
        )
        self._parser.add_argument(
            "--max-concurrent-downloads",
            type=int,
            help="Set the maximum number of concurrent downloads (default: 4)"
        )
        self._parser.add_argument(
            "--filename-template",
            help="Set a customized filename for the downloaded video"
        )
        self._parser.add_argument(
            "--lazy-duplicate-check",
            help="Enable lazy duplicate check by comparing filenames to detect already downloaded videos.",
            action="store_true",
            default=None
        )
        self._parser.add_argument(
            "-v",
            help="Show the app's version",
            action="version",
            version=display_version()
        )
