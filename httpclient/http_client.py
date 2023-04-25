import pprint
from typing import Any

import aiohttp


class HttpClient:
    def __init__(self, base_url: str):
        self._base_url = base_url
        self._client = aiohttp.ClientSession()

    async def close(self):
        await self._client.close()

    async def post(self, url: str, json: Any):
        pprint.pprint(self._client)
        async with self._client.post(self._base_url + url, json=json) as response:
            return await response.json()
