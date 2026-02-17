import asyncio
import sys
from argparse import Namespace

from playwright.async_api import Error as PlaywrightAsyncError
from playwright.sync_api import Error as PlaywrightError

from tikorgzo import app_functions as fn
from tikorgzo import exceptions as exc
from tikorgzo.cli.args_handler import ArgsHandler
from tikorgzo.config.constants import CONFIG_PATH_LOCATIONS
from tikorgzo.config.model import ConfigKey
from tikorgzo.config.provider import ConfigProvider
from tikorgzo.console import console
from tikorgzo.constants import DownloadStatus
from tikorgzo.core.download_manager.queue import DownloadQueueManager
from tikorgzo.core.extractors.context_manager import ExtractorHandler
from tikorgzo.core.session.model import ClientSessionManager
from tikorgzo.core.video.model import Video


async def main() -> None:
    ah = ArgsHandler()
    args = ah.parse_args()

    # Show help/CLI welcome msg if no link or file argument is provided, then exit
    if not args.file and not args.link:
        ah.show_help()
        sys.exit(0)

    config = _load_config(args)
    video_links = _get_video_links(args.file, args.link)

    # Stage 1
    download_queue = _validate_video_links(video_links, config)

    if download_queue.is_empty():
        console.print("\nProgram will now stopped as there is nothing to process.")
        sys.exit(0)

    # Stage 2
    download_queue, session = await _extract_download_links(download_queue, config)

    if download_queue.is_empty():
        console.print("\nThe program will now exit as no links were extracted.")
        await session.close()
        sys.exit(1)

    # Stage 3
    await _download_videos(download_queue, config, session)


def _load_config(args: Namespace) -> ConfigProvider:
    """Build and return the configuration, exiting on invalid data."""
    config = ConfigProvider()

    try:
        config.map_from_cli(args)
        config.map_from_config_file(CONFIG_PATH_LOCATIONS)
    except exc.InvalidConfigDataError as e:
        console.print(f"[red]error:[/red] Invalid config data from {e.source}: {e}")
        sys.exit(1)

    return config


def _get_video_links(file_path: str, links: list[str]) -> set[str]:
    try:
        return fn.extract_video_links(file_path, links)
    except FileNotFoundError:
        console.print(f"[red]error[/red]: '{file_path}' doesn't exist.")
        sys.exit(1)
    except exc.InvalidVideoLinkExtractionError:
        console.print("[red]error:[/red] No valid source of video links provided. Please provide a file path or at least one video link.")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]error:[/red] An unexpected error occurred while extracting video links: {type(e).__name__}: {e}")
        sys.exit(1)


def _validate_video_links(
    video_links: set[str],
    config: ConfigProvider,
) -> DownloadQueueManager:
    """Stage 1 - validate each link and populate the download queue."""
    console.print("[b]Stage 1/3[/b]: Video Link/ID Validation")

    download_queue = DownloadQueueManager()

    for idx, video_link in enumerate(video_links):
        curr_pos = idx + 1
        with console.status(f"Checking video {curr_pos} if already exist..."):
            try:
                video = Video(video_link=video_link, config=config)
                video.download_status = DownloadStatus.QUEUED
                download_queue.add(video)
                console.print(f"Added video {curr_pos} ({video.video_id}) to download queue.")
            except (
                exc.InvalidVideoLinkError,
                exc.VideoFileAlreadyExistsError,
                exc.VideoIDExtractionError,
            ) as e:
                console.print(f"[gray50]Skipping video {curr_pos} due to: [orange1]{type(e).__name__}: {e}[/orange1][/gray50]")
            except PlaywrightError:
                sys.exit(1)
            except Exception as e:
                console.print(f"[gray50]Skipping video {curr_pos} due to: [orange1]{type(e).__name__}: {e}[/orange1][/gray50]")

    return download_queue


async def _extract_download_links(
    download_queue: DownloadQueueManager,
    config: ConfigProvider,
) -> tuple[DownloadQueueManager, ClientSessionManager]:
    """Stage 2 - extract direct download URLs for every queued video."""
    console.print("\n[b]Stage 2/3[/b]: Download Link Extraction")

    session = ClientSessionManager(config.get_value(ConfigKey.EXTRACTOR))

    try:
        extractor = fn.get_extractor(
            config.get_value(ConfigKey.EXTRACTOR),
            config.get_value(ConfigKey.EXTRACTION_DELAY),
            session,
        )
        await extractor.initialize()

        disallow_cleanup = bool(config.get_value(ConfigKey.EXTRACTOR) == 2)  # noqa: PLR2004
        async with ExtractorHandler(extractor, disallow_cleanup=disallow_cleanup) as eh:
            with console.status(f"Extracting links from {download_queue.total()} videos..."):
                results = await eh.process_video_links(download_queue.get_queue())

                successful = [
                    video
                    for video, result in zip(download_queue.get_queue(), results, strict=True)
                    if not isinstance(result, BaseException)
                ]

            download_queue.replace_queue(successful)
    except exc.MissingChromeBrowserError:
        console.print("[red]error:[/red] Google Chrome is not installed in your system. Please install it to proceed.")
        await session.close()
        sys.exit(1)
    except exc.ExtractorCreationError:
        console.print("[red]error:[/red] Invalid extractor/extraction delay/session value provided for extractor creation.")
        await session.close()
        sys.exit(1)
    except (Exception, PlaywrightAsyncError) as e:
        console.print(f"[red]error:[/red] An unexpected error occurred during link extraction: {type(e).__name__}: {e}")
        await session.close()
        sys.exit(1)

    return download_queue, session


async def _download_videos(
    download_queue: DownloadQueueManager,
    config: ConfigProvider,
    session: ClientSessionManager,
) -> None:
    """Stage 3 - download all successfully extracted videos."""
    console.print("\n[b]Stage 3/3[/b]: Download")
    console.print(f"Downloading {download_queue.total()} videos...")

    videos = await fn.download_video(
        config.get_value(ConfigKey.MAX_CONCURRENT_DOWNLOADS),
        download_queue.get_queue(),
        session=session,
    )
    fn.cleanup_interrupted_downloads(videos)
    fn.print_download_results(videos)
    await session.close()


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
