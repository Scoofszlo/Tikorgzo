import argparse
from rich_argparse import RichHelpFormatter


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
