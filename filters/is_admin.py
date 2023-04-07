import logging

from aiogram import types
from aiogram.filters import BaseFilter

from db.repository.user_repo import UserRepo

logger = logging.getLogger(__name__)


class IsChatAdmin(BaseFilter):

    async def __call__(self, message: types.Message, user_repo: UserRepo) -> bool:
        user_id = message.from_user.id
        chat_id = message.chat.id
        isAdmin = await user_repo.is_admin(user_id=user_id, chat_id=chat_id)

        logger.debug(f"User with id:{user_id} is Admin for chat with chat_id:{chat_id}, result: {isAdmin}")

        return isAdmin
