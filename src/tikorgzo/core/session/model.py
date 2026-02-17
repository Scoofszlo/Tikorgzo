import aiohttp
import requests

from tikorgzo.constants import TIKWM_EXTRACTOR_NAME


class ClientSessionManager:
    """Manages the client session used for both extraction and downloading, ensuring proper cleanup."""

    def __init__(self, extractor: str) -> None:
        self.client_session = self._get_session(extractor)

    async def close(self) -> None:
        if hasattr(self.client_session, "close"):
            if isinstance(self.client_session, aiohttp.ClientSession):
                await self.client_session.close()
            else:
                self.client_session.close()

    def _get_session(self, extractor: str) -> requests.Session | aiohttp.ClientSession:
        """Get a requests Session or aiohttp ClientSession depending on the chosen link extractor."""

        if extractor == TIKWM_EXTRACTOR_NAME:
            return aiohttp.ClientSession()

        return requests.Session()
