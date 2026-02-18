from tikorgzo.core.download_manager.strategies._base import BaseDownloadStrategy
from tikorgzo.core.download_manager.strategies.aiohttp import AioHTTPDownloadStrategy
from tikorgzo.core.download_manager.strategies.requests import RequestsDownloadStrategy

__all__ = [
    "AioHTTPDownloadStrategy",
    "BaseDownloadStrategy",
    "RequestsDownloadStrategy",
]
