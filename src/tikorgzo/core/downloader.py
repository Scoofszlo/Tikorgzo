import requests
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from tikorgzo.console import console
from tikorgzo.core.video_info import FileSize


class Downloader:
    def download(
            self,
            link: str,
            video_file: str,
            file_size: FileSize
    ) -> None:
        console.print(f"Attempting to download video from: {link}")

        try:
            response = requests.get(link, stream=True)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            total_size = file_size.get()

            assert isinstance(total_size, int)

            with Progress(
                TextColumn("[cyan]Downloading..."),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task("[cyan]Downloading...", total=total_size)
                with open(video_file, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            progress.update(task, advance=len(chunk))

            console.print(f"Video downloaded successfully to: {video_file}\n")
        except requests.exceptions.RequestException as e:
            console.print(f"Error downloading video: {e}")
