import os

from platformdirs import user_downloads_path


APP_NAME = "tikorgzo"
DOWNLOAD_PATH = os.path.join(user_downloads_path(), APP_NAME)
