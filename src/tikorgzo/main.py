from playwright.sync_api import Error as PlaywrightError

from tikorgzo import exceptions as exc
from tikorgzo.args_handler import ArgsHandler
from tikorgzo.console import console
from tikorgzo.core import functions as fn
from tikorgzo.core.video.model import Video
from tikorgzo.utils import video_link_extractor, remove_file


def run():
    ah = ArgsHandler()
    args = ah.parse_args()

    video_links = video_link_extractor(args.file, args.link)

    for idx, video_link in enumerate(video_links):
        video = None

        while True:
            curr_pos = idx + 1
            total_links = len(video_links)

            console.print(f"Downloading video from {video_link} ({curr_pos}/{total_links})...")

            try:
                video = Video(video_link)
                fn.extract_download_link(video)
                video.print_video_details()
                fn.download_video(video)
                break
            except (
                exc.DownloadError,
                exc.FileTooLargeError,
                exc.HrefLinkMissingError,
                exc.HtmlElementMissingError,
                exc.InvalidVideoLink,
                exc.URLParsingError,
                exc.VideoIDExtractionError,
            ) as e:
                console.print(f"Skipping due to: [red]{type(e).__name__}: {e}[/red]\n")
                break
            except exc.VideoFileAlreadyExistsError as e:
                console.print(f"Skipping due to: [orange1]{type(e).__name__}: {e}[/orange1]\n")
                break
            except exc.ExtractionTimeoutError as e:
                console.print(f"Retrying due to: [orange1]{type(e).__name__}: {e}[/orange1]\n")
                continue
            except KeyboardInterrupt:
                if curr_pos == total_links:
                    console.print("Cancelling current download...")
                else:
                    console.print("Cancelling current download and remaining queue...")
                remove_file(video)
                exit(1)
            except PlaywrightError:
                exit(1)
