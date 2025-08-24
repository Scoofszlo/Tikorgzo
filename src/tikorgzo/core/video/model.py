from dataclasses import dataclass
from rich.panel import Panel
from typing import Optional

from tikorgzo.console import console
from tikorgzo.core.video.processor import VideoInfoProcessor
from tikorgzo.exceptions import FileTooLargeError


USERNAME_REGEX = r"\/@([\w\.\-]+)\/video\/\d+"
NORMAL_TIKTOK_VIDEO_LINK_REGEX = r"https?://(www\.)?tiktok\.com/@[\w\.\-]+/video/\d+(\?.*)?$"
VT_TIKTOK_VIDEO_LINK_REGEX = r"https?://vt\.tiktok\.com/"


processor = VideoInfoProcessor()


class Video:
    """
    Video class that handles the information of a TikTok video

    Attributes:
        _video_id (Optional[int]): The unique identifier for the video.
        _username (Optional[str]): The username associated with the video.
        _video_link (str): The normalized video link.
        _download_link (Optional[str]): The source quality download link of the video.
        _file_size (Optional[FileSize]): The size of the video file.
        _output_file_dir (Optional[str]): Directory where the video will be saved.
        _output_file_path (Optional[str]): Full path to the output video file.
    Args:
        video_link (str): The TikTok video link or video ID.
    Raises:
        InvalidVideoLink: If the provided video link is not valid.
        VideoFileAlreadyExistsError: If the video file already exists in the output directory.
    """

    def __init__(self, video_link: str):
        video_link = processor.validate_video_link(video_link)

        self._video_id: Optional[int] = processor.extract_video_id(video_link)

        processor.check_if_already_downloaded(video_link)

        self._username = processor._process_username(video_link)
        self._video_link = video_link
        self._download_link: Optional[str] = None
        self._file_size: Optional[FileSize] = None
        self._output_file_dir: Optional[str] = None
        self._output_file_path: Optional[str] = None
        processor.process_output_paths(self)

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username: str):
        if username.startswith("@"):
            self._username = username[1:]
        else:
            self._username = username

    @property
    def video_link(self):
        assert self._video_link is not None
        return self._video_link

    @property
    def download_link(self):
        assert self._download_link is not None
        return self._download_link

    @download_link.setter
    def download_link(self, download_link: str):
        self._download_link = download_link
        self._video_id = processor.extract_video_id(download_link)

    @property
    def video_id(self):
        assert self._video_id is not None
        return self._video_id

    @property
    def file_size(self):
        assert self._file_size is not None
        return self._file_size

    @file_size.setter
    def file_size(self, file_size: int):
        self._file_size = FileSize(file_size)

    @property
    def output_file_dir(self):
        assert self._output_file_dir is not None
        return self._output_file_dir

    @property
    def output_file_path(self):
        assert self._output_file_path is not None
        return self._output_file_path

    def print_video_details(self):
        console.print(Panel.fit(
            (
                f"Username: {self.username}\n"
                f"Video URL: {self.video_link}\n"
                f"Download URL: {self._download_link}\n"
                f"File Size: {self.file_size.get(formatted=True)}"
            ),
            title="Video details"
        ))


@dataclass
class FileSize:
    size_in_bytes: int

    def get(self, formatted: bool = False) -> int | str:
        """
        Returns the file size.
        If formatted=True, returns a human-readable string (e.g., '1.23 MB').
        If formatted=False, returns the raw float value in bytes.
        """
        if not formatted:
            return self.size_in_bytes

        size = self.size_in_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

        raise FileTooLargeError()
