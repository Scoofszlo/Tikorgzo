import pathlib

import requests

from tikorgzo.cli.text_printer import console
from tikorgzo.constants import DIRECT_EXTRACTOR_NAME, STATUS_OK, TIKWM_EXTRACTOR_NAME, DownloadStatus
from tikorgzo.core.extractors.direct.extractor import DirectExtractor
from tikorgzo.core.extractors.tikwm.extractor import TikWMExtractor
from tikorgzo.core.session.model import ClientSessionManager
from tikorgzo.core.video.model import Video
from tikorgzo.exceptions import ExtractorCreationError, InvalidProxyError, InvalidVideoLinkExtractionError


def extract_video_links(file_path: str | None, links: list[str]) -> set[str]:
    """Extracts the video links based from a list of strings or from a file."""

    if file_path:
        try:
            with pathlib.Path(file_path).open("r", encoding="utf-8") as f:
                return {line.strip() for line in f if line.strip()}
        except FileNotFoundError as e:
            raise FileNotFoundError from e

    elif links:
        return set(links)

    raise InvalidVideoLinkExtractionError


def is_proxy_valid(value: str) -> None:
    proxies = {
        "http": value,
        "https": value,
    }

    try:
        response = requests.get("https://ifconfig.me/ip", proxies=proxies, timeout=30)

        if response.status_code != STATUS_OK:
            raise InvalidProxyError(value)
    except (
        requests.exceptions.ProxyError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    ) as e:
        raise InvalidProxyError(value) from e


def get_extractor(
        extractor: str,
        extraction_delay: float,
        proxy: str | None,
        session: ClientSessionManager,
) -> "TikWMExtractor | DirectExtractor":
    if extractor == TIKWM_EXTRACTOR_NAME:
        return TikWMExtractor(extraction_delay, proxy=proxy)
    if extractor == DIRECT_EXTRACTOR_NAME and isinstance(session.client_session, requests.Session):
        return DirectExtractor(extraction_delay, session.client_session)
    raise ExtractorCreationError


def print_download_results(videos: list[Video]) -> None:
    unstarted_downloads = 0
    failed_downloads = 0
    successful_downloads = 0
    result_msg = "\nFinished downloads with "
    use_comma_separator = False

    for video in videos:
        if video.download_status == DownloadStatus.QUEUED:
            unstarted_downloads += 1
        if video.download_status == DownloadStatus.INTERRUPTED:
            failed_downloads += 1
        elif video.download_status == DownloadStatus.COMPLETED:
            successful_downloads += 1

    if successful_downloads >= 1:
        result_msg += f"[green]{successful_downloads} successful[/green]"
        use_comma_separator = True
    if failed_downloads >= 1:
        if use_comma_separator:
            result_msg += f", [red]{failed_downloads} failed[/red]"
        else:
            result_msg += f"[red]{failed_downloads} failed[/red]"
            use_comma_separator = True
    if unstarted_downloads >= 1:
        if use_comma_separator:
            result_msg += f", [orange1]{unstarted_downloads} unstarted[/orange1]"
        else:
            result_msg += f"[orange1]{unstarted_downloads} unstarted[/orange1]"

    console.print(result_msg)
