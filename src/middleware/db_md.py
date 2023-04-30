from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.db.database import Database
from src.db.repository.chat_repo import ChatRepo
from src.db.repository.stop_word_repo import StopWordRepo
from src.db.repository.user_repo import UserRepo


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data['user_repo'] = UserRepo(session)
            data['chat_repo'] = ChatRepo(session)
            data['sw_repo'] = StopWordRepo(session)
            data["db"] = Database(session)
            result = await handler(event, data)
            return result
