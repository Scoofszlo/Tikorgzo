from enum import StrEnum


class ConfigKey(StrEnum):
    FILE = "file"
    LINK = "link"
    MAX_CONCURRENT_DOWNLOADS = "max_concurrent_downloads"
    FILENAME_TEMPLATE = "filename_template"
    LAZY_DUPLICATE_CHECK = "lazy_duplicate_check"
