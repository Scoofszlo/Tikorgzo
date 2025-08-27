import requests
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from tikorgzo.console import console
from tikorgzo.core.video.model import FileSize
from tikorgzo.exceptions import DownloadError


class Downloader:
    def download(
            self,
            download_link: str,
            output_file_path: str,
            file_size: FileSize
    ) -> None:
        console.print(f"Attempting to download video from: {download_link}")

        try:
            response = requests.get(download_link, stream=True)
            response.raise_for_status()
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
                with open(output_file_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            progress.update(task, advance=len(chunk))

            console.print(f"Video downloaded successfully to: {output_file_path}\n")

        except Exception as e:
            raise DownloadError(e)
