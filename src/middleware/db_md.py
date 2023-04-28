import pprint
from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

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
        # model: BertToxicityClassifier = get_model()
        # data['model'] = model

        async with self.session_pool() as session:
            # pprint.pprint("Open session")
            # pprint.pprint(session)
            data['user_repo'] = UserRepo(session)
            data['chat_repo'] = ChatRepo(session)
            data['sw_repo'] = StopWordRepo(session)
            data["db"] = Database(session)
            result = await handler(event, data)
            # pprint.pprint("Close session")
            session: AsyncSession
            # pprint.pprint(session.is_active)
            return result
