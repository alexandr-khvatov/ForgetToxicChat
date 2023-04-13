import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from db.models.userchat import UserChat
from db.repository.user_repo import UserRepo

logger = logging.getLogger(__name__)


async def fetch_admins(user_repo: UserRepo, bot: Bot) -> None:
    logger.info(f"Start refreshing admin list after reboot, bot with id:{bot.id}")
    chat_ids = await user_repo.get_all_chat_when_bot_admin(user_id=bot.id)
    if chat_ids is not None:
        for chat_id in chat_ids:
            try:
                admins = await bot.get_chat_administrators(chat_id=chat_id, request_timeout=10)
                admin_models = list(map(lambda a: UserChat(user_tg_id=a.user.id, chat_tg_id=chat_id, isAdmin=True), admins))
                await user_repo.update_or_insert_all(admin_models)
            except TelegramBadRequest as ex:
                logger.error(f'Exception get_chat_administrators: {ex.message}')
                pass

    logger.info("Completed updating the list of administrators after a reboot")
