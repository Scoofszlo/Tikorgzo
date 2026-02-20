from enum import StrEnum


class ConfigKey(StrEnum):
    FILE = "file"
    LINK = "link"
    EXTRACTOR = "extractor"
    DOWNLOAD_DIR = "download_dir"
    EXTRACTION_DELAY = "extraction_delay"
    MAX_CONCURRENT_DOWNLOADS = "max_concurrent_downloads"
    FILENAME_TEMPLATE = "filename_template"
    LAZY_DUPLICATE_CHECK = "lazy_duplicate_check"
    PROXY = "proxy"
