import asyncio
from playwright.sync_api import Error as PlaywrightError

from tikorgzo import exceptions as exc
from tikorgzo.args_handler import ArgsHandler
from tikorgzo.console import console
from tikorgzo.core import functions as fn
from tikorgzo.core.extractor import Extractor
from tikorgzo.core.video.model import Video
from tikorgzo.utils import video_link_extractor


async def main():
    ah = ArgsHandler()
    args = ah.parse_args()

    if not args.file and not args.link:
        console.print("[red]No input file or link supplied.[/red]\nRun 'tikorgzo -h' for more details.")
        exit(1)

    # Get the video IDs
    video_links = video_link_extractor(args.file, args.link)
    video_links_len = len(video_links)

    # Contains the list of Video objects that will be used for processing
    download_queue: list[Video] = []
    download_queue_len: int

    # Initialize the video objects with the video IDs extracted from video_links
    console.print("[b]Stage 1/3[/b]: Video Link/ID Validation")

    for idx, video_link in enumerate(video_links):
        while True:
            curr_pos = idx + 1
            with console.status(f"Checking video {curr_pos} if already exist..."):
                try:
                    video = Video(video_link=video_link)
                    download_queue.append(video)
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
                    exit(1)

    if not len(download_queue) >= 1:
        console.print("\nProgram will now stopped as there is nothing to process.")
        exit(0)

    download_queue_len = len(download_queue)

    async with Extractor() as bm:
        console.print("\n[b]Stage 2/3[/b]: Download Link Extraction")
        with console.status(f"Extracting links from {download_queue_len} videos..."):

            # Extracts video asynchronously
            results = await bm.process_video_links(download_queue)

            successful_tasks = []

            for video, result in zip(download_queue, results):
                # If any kind of exception (URLParsingError or any HTML-related exceptions,
                # they will be skipped based on this condition and will print the error.
                # Otherwise, it will append it to the successful_videos list then replaces
                # the videos that holds the Video objects
                if isinstance(result, BaseException):
                    pass
                else:
                    successful_tasks.append(video)

    download_queue = successful_tasks
    download_queue_len = len(download_queue)

    console.print(f"\n[b]Stage 3/3[/b]: Downloading {download_queue_len} videos...")

    for idx, video in enumerate(download_queue):
        curr_pos = idx + 1

        console.print(f"Downloading video from {video.video_link} ({curr_pos}/{download_queue_len})...")

        video.print_video_details()
        fn.download_video(video)


def run():
    asyncio.run(main())
