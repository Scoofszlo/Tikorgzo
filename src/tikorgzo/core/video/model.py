from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from tikorgzo.config.model import ConfigKey
from tikorgzo.config.provider import ConfigProvider
from tikorgzo.constants import DownloadStatus
from tikorgzo.core.video.processor import VideoInfoProcessor
from tikorgzo.exceptions import FileSizeNotSetError, FileTooLargeError


USERNAME_REGEX = r"\/@([\w\.\-]+)\/video\/\d+"
NORMAL_TIKTOK_VIDEO_LINK_REGEX = r"https?://(www\.)?tiktok\.com/@[\w\.\-]+/video/\d+(\?.*)?$"
VT_TIKTOK_VIDEO_LINK_REGEX = r"https?://vt\.tiktok\.com/"


processor = VideoInfoProcessor()


class Video:
    """
    Video class that handles the information of a TikTok video.

    Attributes:
        _config (ConfigProvider): The configuration provider instance that holds the app's configuration.
        _video_link (str): The normalized video link.
        _video_id (int): The unique identifier for the video.
        _username (Optional[str]): The username associated with the video.
        _date (datetime): The date the video was uploaded.
        _download_link (Optional[str]): The source quality download link of the video.
        _file_size (Optional[FileSize]): The size of the video file.
        _download_status (Optional[DownloadStatus]): The current download status of the Video object.
        _filename_template (Optional[str]): Holds the passed filename template parameter.
        _output_file_dir (Optional[str]): Directory where the video will be saved.
        _output_file_path (Optional[str]): Full path to the output video file.

    Args:
        video_link (str): The TikTok video link or video ID.
        config (ConfigProvider): The configuration provider instance that holds the app's configuration.

    Raises:
        InvalidVideoLink: If the provided video link is not valid.
        VideoFileAlreadyExistsError: If the video file already exists in the output directory.
    """

    def __init__(
        self,
        video_link: str,
        config: ConfigProvider,
    ):
        self._config = config
        self._video_link = processor.validate_video_link(video_link)
        self._video_id: int = processor.extract_video_id(video_link)

        processor.check_if_already_downloaded(
            video_id=self._video_id,
            lazy_duplicate_check=config.get_value(ConfigKey.LAZY_DUPLICATE_CHECK),
            custom_download_dir=config.get_value(ConfigKey.DOWNLOAD_DIR),
        )

        self._username: Optional[str] = processor._process_username(video_link)
        self._date: datetime = processor.get_date(self._video_id)
        self._download_link: Optional[str] = None
        self._file_size = FileSize()
        self._download_status = DownloadStatus.UNSTARTED
        self._filename_template: Optional[str] = config.get_value(ConfigKey.FILENAME_TEMPLATE)
        self._output_file_dir: Optional[str] = None
        self._output_file_path: Optional[str] = None
        processor.process_output_paths(self)

    @property
    def username(self) -> Optional[str]:
        return self._username

    @username.setter
    def username(self, username: str) -> None:
        if username.startswith("@"):
            self._username = username[1:]
        else:
            self._username = username

    @property
    def video_link(self) -> str:
        return self._video_link

    @property
    def download_link(self) -> str:
        assert self._download_link is not None
        return self._download_link

    @download_link.setter
    def download_link(self, download_link: str) -> None:
        self._download_link = download_link
        self._video_id = processor.extract_video_id(download_link)

    @property
    def video_id(self) -> int:
        return self._video_id

    @property
    def file_size(self) -> "FileSize":
        return self._file_size

    @file_size.setter
    def file_size(self, file_size: float) -> None:
        self._file_size.update(file_size)

    @property
    def download_status(self) -> DownloadStatus:
        return self._download_status

    @download_status.setter
    def download_status(self, download_status: DownloadStatus) -> None:
        self._download_status = download_status

    @property
    def output_file_dir(self) -> Optional[str]:
        return self._output_file_dir

    @property
    def output_file_path(self) -> str:
        assert self._output_file_path is not None
        return self._output_file_path


@dataclass
class FileSize:
    size_in_bytes: Optional[float] = None

    def get(self, formatted: bool = False) -> float | str:
        """
        Returns the file size.
        If formatted=True, returns a human-readable string (e.g., '1.23 MB').
        If formatted=False, returns the raw float value in bytes.
        """
        if self.size_in_bytes is None:
            raise FileSizeNotSetError()

        if not formatted:
            return self.size_in_bytes

        size = self.size_in_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0

        raise FileTooLargeError()

    def update(self, value: float) -> None:
        self.size_in_bytes = value
