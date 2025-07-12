from tikorgzo import ArgsHandler
from tikorgzo import console
from tikorgzo import exceptions as exc
from tikorgzo import functions as fn
from tikorgzo import VideoInfo


def run():
    ah = ArgsHandler()
    args = ah.parse_args()

    links = []

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]

    elif args.link:
        for link in args.link:
            links.append(link)

    for idx, video_link in enumerate(links):
        curr_pos = idx + 1
        total_links = len(links)

        console.print(f"Downloading video from {video_link} ({curr_pos}/{total_links})...")

        try:
            vid_info = VideoInfo(video_link)
            fn.update_metadata(vid_info)
            vid_info.print_video_details()
            fn.download_video(vid_info)
        except (
            exc.FileTooLargeError,
            exc.HrefLinkMissingError,
            exc.HtmlElementMissingError,
            exc.InvalidVideoLink,
            exc.URLParsingError,
            exc.VideoIDExtractionError,
        ) as e:
            console.print(f"Skipping due to: [red]{type(e).__name__}: {e}[/red]\n")
            continue
        except exc.VideoFileAlreadyExistsError as e:
            console.print(f"Skipping due to: [orange1]{type(e).__name__}: {e}[/orange1]\n")
            continue
