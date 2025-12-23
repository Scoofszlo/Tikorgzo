import asyncio
import sys
from playwright.sync_api import Error as PlaywrightError
from playwright.async_api import Error as PlaywrightAsyncError

from tikorgzo import exceptions as exc
from tikorgzo import generic as fn
from tikorgzo.cli.args_handler import ArgsHandler
from tikorgzo.cli.args_validator import validate_args
from tikorgzo.config.model import ConfigKey
from tikorgzo.config.provider import ConfigProvider
from tikorgzo.config.constants import CONFIG_PATH_LOCATIONS
from tikorgzo.console import console
from tikorgzo.constants import DownloadStatus
from tikorgzo.core.download_link_extractor import Extractor
from tikorgzo.core.download_manager.queue import DownloadQueueManager
from tikorgzo.core.video.model import Video


async def main() -> None:
    ah = ArgsHandler()
    args = ah.parse_args()

    validate_args(ah, args)

    config = ConfigProvider()
    config.map_from_cli(args)
    config.map_from_config_file(CONFIG_PATH_LOCATIONS)

    # Get the video IDs
    file_path = args.file
    link_list = args.link

    video_links = fn.extract_video_links(file_path, link_list)
    download_queue = DownloadQueueManager()

    console.print("[b]Stage 1/3[/b]: Video Link/ID Validation")

    for idx, video_link in enumerate(video_links):
        while True:
            curr_pos = idx + 1
            with console.status(f"Checking video {curr_pos} if already exist..."):
                try:
                    video = Video(video_link=video_link, config=config)
                    video.download_status = DownloadStatus.QUEUED
                    download_queue.add(video)
                    console.print(f"Added video {curr_pos} ({video.video_id}) to download queue.")
                    break
                except (
                    exc.InvalidVideoLink,
                    exc.VideoFileAlreadyExistsError,
                    exc.VideoIDExtractionError,
                ) as e:
                    console.print(f"[gray50]Skipping video {curr_pos} due to: [orange1]{type(e).__name__}: {e}[/orange1][/gray50]")
                    break
                except PlaywrightError:
                    sys.exit(1)
                except Exception as e:
                    console.print(f"[gray50]Skipping video {curr_pos} due to: [orange1]{type(e).__name__}: {e}[/orange1][/gray50]")
                    break

    if download_queue.is_empty():
        console.print("\nProgram will now stopped as there is nothing to process.")
        sys.exit(0)

    console.print("\n[b]Stage 2/3[/b]: Download Link Extraction")

    try:
        async with Extractor() as extr:
            with console.status(f"Extracting links from {download_queue.total()} videos..."):

                # Extracts video asynchronously
                results = await extr.process_video_links(download_queue.get_queue())

                successful_tasks = []

                for video, result in zip(download_queue.get_queue(), results):
                    # If any kind of exception (URLParsingError or any HTML-related exceptions,
                    # they will be skipped based on this condition.
                    # Otherwise, this will be appended to successful_videos list then replaces
                    # the videos that holds the Video objects
                    if isinstance(result, BaseException):
                        pass
                    else:
                        successful_tasks.append(video)

            download_queue.replace_queue(successful_tasks)
    except exc.MissingChromeBrowserError:
        console.print("[red]error:[/red] Google Chrome is not installed in your system. Please install it to proceed.")
        sys.exit(1)
    except (
        Exception,
        PlaywrightAsyncError
    ) as e:
        console.print(f"[red]error:[/red] An unexpected error occurred during link extraction: {type(e).__name__}: {e}")
        sys.exit(1)

    if download_queue.is_empty():
        console.print("\nThe program will now exit as no links were extracted.")
        sys.exit(1)

    console.print("\n[b]Stage 3/3[/b]: Download")
    console.print(f"Downloading {download_queue.total()} videos...")

    videos = await fn.download_video(config.get_value(ConfigKey.MAX_CONCURRENT_DOWNLOADS), download_queue.get_queue())
    fn.cleanup_interrupted_downloads(videos)
    fn.print_download_results(videos)


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
