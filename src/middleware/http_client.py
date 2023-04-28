from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class HttpClientMiddleware(BaseMiddleware):
    def __init__(self, httpclient):
        super().__init__()
        self.httpclient = httpclient

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        data['httpclient'] = self.httpclient
        return await handler(event, data)
