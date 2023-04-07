from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from db.repository.chat_repo import ChatRepo
from db.repository.stop_word_repo import StopWordRepo
from db.repository.user_repo import UserRepo
from services.toxicity.BertToxicityClassifier import BertToxicityClassifier, get_model


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
        model: BertToxicityClassifier = get_model()
        data['model'] = model
        async with self.session_pool() as session:
            data["session"] = session
            data['user_repo'] = UserRepo(session)
            data['chat_repo'] = ChatRepo(session)
            data['sw_repo'] = StopWordRepo(session)
            return await handler(event, data)
