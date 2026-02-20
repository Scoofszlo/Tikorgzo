from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from tikorgzo.config.model import ConfigKey
from tikorgzo.config.provider import ConfigProvider
from tikorgzo.constants import DownloadStatus
from tikorgzo.core.video import helpers as fn
from tikorgzo.exceptions import FileSizeNotSetError, FileTooLargeError

if TYPE_CHECKING:
    from datetime import datetime

USERNAME_REGEX = r"\/@([\w\.\-]+)\/video\/\d+"
NORMAL_TIKTOK_VIDEO_LINK_REGEX = r"https?://(www\.)?tiktok\.com/@[\w\.\-]+/video/\d+(\?.*)?$"
VT_TIKTOK_VIDEO_LINK_REGEX = r"https?://vt\.tiktok\.com/"

# File size conversion constant
BYTES_PER_KB = 1024.0


class Video:
    # pylint: disable=too-many-instance-attributes
    """Represents a TikTok video and its associated metadata.

    On construction, the provided link is normalized (full links are kept as-is,
    shortened vt.tiktok.com links are resolved to their full form, and bare 19-digit
    video IDs are accepted directly). The video ID, username, and upload date are then
    extracted from the normalized link, duplicate-download checks are performed, and
    output paths are assigned.

    Attributes:
        config (ConfigProvider): The configuration provider instance.
        _video_link (str): The normalized TikTok video link (or bare video ID).
        _video_id (int): The 19-digit unique identifier for the video.
        _username (str | None): The creator's username, if present in the link.
        _date (datetime): The upload date derived from the video ID.
        _download_link (str | None): The resolved direct download URL, set by an extractor.
        _file_size (FileSize): The size of the video file, set after the download link is resolved.
        _download_status (DownloadStatus): The current download status of the video.
        _filename_template (str | None): Custom filename template passed via config or CLI.
        _output_file_dir (Path | None): Directory where the video will be saved.
        _output_file_path (Path | None): Full path to the output video file.

    Args:
        video_link (str): A full TikTok video URL, a shortened vt.tiktok.com URL, or a bare 19-digit video ID.
        config (ConfigProvider): The configuration provider instance.

    Raises:
        InvalidVideoLinkError: If the provided video link cannot be normalized.
        VideoFileAlreadyExistsError: If the video has already been downloaded.

    """

    def __init__(
        self,
        video_link: str,
        config: ConfigProvider,
    ) -> None:
        self.config = config
        self._video_link = fn.normalize_video_link(video_link, config.get_value(ConfigKey.PROXY))
        self._video_id: int = fn.extract_video_id(video_link)

        fn.check_if_already_downloaded(
            video_id=self._video_id,
            lazy_duplicate_check=config.get_value(ConfigKey.LAZY_DUPLICATE_CHECK),
            custom_download_dir=config.get_value(ConfigKey.DOWNLOAD_DIR),
        )

        self._username: str | None = fn.process_username(video_link)
        self._date: datetime = fn.get_date(self._video_id)
        self._download_link: str | None = None
        self._file_size = FileSize()
        self._download_status = DownloadStatus.UNSTARTED
        self._filename_template: str | None = config.get_value(ConfigKey.FILENAME_TEMPLATE)
        self._output_file_dir: Path | None = None
        self._output_file_path: Path | None = None
        fn.assign_output_paths(self)

    @property
    def username(self) -> str | None:
        return self._username

    @username.setter
    def username(self, username: str) -> None:
        if username.startswith("@"):
            self._username = username[1:]
        else:
            self._username = username

    @property
    def date(self) -> "datetime":
        return self._date

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

    @property
    def video_id(self) -> int:
        return self._video_id

    @video_id.setter
    def video_id(self, video_id: int) -> None:
        self._video_id = video_id

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
    def filename_template(self) -> str | None:
        return self._filename_template

    @property
    def output_file_dir(self) -> Path | None:
        return self._output_file_dir

    @output_file_dir.setter
    def output_file_dir(self, output_file_dir: Path) -> None:
        self._output_file_dir = output_file_dir

    @property
    def output_file_path(self) -> Path:
        assert self._output_file_path is not None
        return self._output_file_path

    @output_file_path.setter
    def output_file_path(self, output_file_path: Path) -> None:
        self._output_file_path = output_file_path


@dataclass
class FileSize:
    size_in_bytes: float | None = None

    def get(self, formatted: bool = False) -> float | str:
        """Returns the file size.
        If formatted=True, returns a human-readable string (e.g., '1.23 MB').
        If formatted=False, returns the raw float value in bytes.
        """
        if self.size_in_bytes is None:
            raise FileSizeNotSetError

        if not formatted:
            return self.size_in_bytes

        size = self.size_in_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if size < BYTES_PER_KB:
                return f"{size:.2f} {unit}"
            size /= BYTES_PER_KB

        raise FileTooLargeError

    def update(self, value: float) -> None:
        self.size_in_bytes = value
