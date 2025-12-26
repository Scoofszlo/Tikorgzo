from typing import Optional


class MissingPlaywrightBrowserError(Exception):
    """Raised when Playwright browser to be used for extraction hasn't been installed."""

    def __init__(self) -> None:
        self.message = "Playwright browser hasn't been installed. Run 'uvx playwright install' to install the browser."
        super().__init__(self.message)


class MissingChromeBrowserError(Exception):
    """Raised when Chrome browser to be used for extraction hasn't been installed."""

    def __init__(self) -> None:
        self.message = "Chrome browser isn't installed on this system. Please install Chrome to proceed."
        super().__init__(self.message)


class InvalidLinkSourceExtractionError(Exception):
    """Raised when there is no specified link or file for processing of links."""

    def __init__(self) -> None:
        self.message = "Path to the list of links or links must be supplied."
        super().__init__(self.message)


class InvalidVideoLink(Exception):
    """Raised when the video link specified is invalid."""

    def __init__(self, video_link: str) -> None:
        self.message = f"Video link '{video_link}' is not valid. Please check again."
        super().__init__(self.message)


class InvalidDateFormat(Exception):
    """Raised when invalid date format is used."""

    def __init__(self) -> None:
        self.message = "Date format is invalid. Please ensure your format is correct by checking the supported formats here: https://strftime.org/"
        super().__init__(self.message)


class VideoFileAlreadyExistsError(Exception):
    """Raised when the requested video file to download already exists in the downloads folder"""

    def __init__(self, vid_file: str, username: Optional[str] = None) -> None:
        if username:
            self.message = f"Video '{vid_file}' (@{username}) already exists."
        else:
            self.message = f"Video '{vid_file}` already exists."
        super().__init__(self.message)


class VideoIDExtractionError(Exception):
    """Raised when video ID can't be extracted from the video link."""

    def __init__(self) -> None:
        self.message = "Video ID can't be extracted."
        super().__init__(self.message)


class HtmlElementMissingError(Exception):
    """Raised when a required HTML element is missing during scraping."""

    def __init__(self, element_description: str) -> None:
        self.message = f"HTML element wasn't found: {element_description}, or the website may be slow at the moment."
        super().__init__(self.message)


class URLParsingError(Exception):
    """Raised when the video URL provided is invalid, most likely a mistyped
    link or the video has been deleted."""

    def __init__(self) -> None:
        self.message = "Video URL is invalid. Please check for typos or if it's still publicly available."
        super().__init__(self.message)


class VagueErrorMessageError(Exception):
    """Raised when the API raises vague 'error` message when extracting the download link of a video."""

    def __init__(self) -> None:
        self.message = "A vague 'error' message banner pops up. Please try downloading again."
        super().__init__(self.message)


class HrefLinkMissingError(Exception):
    """Custom exception when the href link of download button doesn't exist."""

    def __init__(self) -> None:
        self.message = "Could not find the 'href' attribute on the download link element."
        super().__init__(self.message)


class FileSizeNotSetError(Exception):
    """Raised when FileSize doesn't have yet file size value, but something attempts to get the
    value through its `get()`.
    """

    def __init__(self) -> None:
        self.message = "File size has not been set yet."
        super().__init__(self.message)


class FileTooLargeError(Exception):
    """Raised when file is way too large, although this isn't likely to happen."""

    def __init__(self) -> None:
        self.message = "File size is way too large."
        super().__init__(self.message)


class DownloadError(Exception):
    """Raised when downloading the video goes wrong."""

    def __init__(self, e: Exception) -> None:
        self.message = f"Error downloading video: {e}"
        super().__init__(self.message)


class ExtractionTimeoutError(Exception):
    """Raised when extracting the download link takes too long."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
