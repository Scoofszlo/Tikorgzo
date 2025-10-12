import asyncio
import sys
from playwright.sync_api import Error as PlaywrightError

from tikorgzo import exceptions as exc
from tikorgzo import generic as fn
from tikorgzo.cli.args_handler import ArgsHandler
from tikorgzo.cli.args_validator import validate_args
from tikorgzo.console import console
from tikorgzo.constants import DownloadStatus
from tikorgzo.core.download_link_extractor import Extractor
from tikorgzo.core.download_manager.queue import DownloadQueueManager
from tikorgzo.core.video.model import Video


async def main() -> None:
    ah = ArgsHandler()
    args = ah.parse_args()

    validate_args(ah, args)

    # Get the video IDs
    video_links = fn.extract_video_links(args.file, args.link)
    download_queue = DownloadQueueManager()

    console.print("[b]Stage 1/3[/b]: Video Link/ID Validation")

    for idx, video_link in enumerate(video_links):
        while True:
            curr_pos = idx + 1
            with console.status(f"Checking video {curr_pos} if already exist..."):
                try:
                    video = Video(video_link=video_link, filename_template=args.filename_template, lazy_duplicate_check=args.lazy_duplicate_check)
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
    except exc.MissingPlaywrightBrowserError:
        console.print("[red]error:[/red] Playwright browser hasn't been installed. Run [b]'uvx playwright install'[/b] to install the browser.")
        sys.exit(1)

    if download_queue.is_empty():
        console.print("\nThe program will now exit as no links were extracted.")
        sys.exit(1)

    console.print("\n[b]Stage 3/3[/b]: Download")
    console.print(f"Downloading {download_queue.total()} videos...")

    videos = await fn.download_video(args.max_concurrent_downloads, download_queue.get_queue())
    fn.cleanup_interrupted_downloads(videos)
    fn.print_download_results(videos)


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
