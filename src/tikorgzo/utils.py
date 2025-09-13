from importlib.metadata import version

from tikorgzo.constants import APP_NAME


def display_version() -> str:
    return f"{APP_NAME} v{version(APP_NAME)}"
