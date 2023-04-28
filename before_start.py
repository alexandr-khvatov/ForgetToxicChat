import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from src.db.models.userchat import UserChat
from src.db.repository.user_repo import UserRepo

logger = logging.getLogger(__name__)


async def fetch_admins(user_repo: UserRepo, bot: Bot) -> None:
    logger.info(f"Start refreshing admin list after reboot, bot with id:{bot.id}")
    chat_ids = await user_repo.get_all_chat_when_bot_admin(user_id=bot.id)
    if chat_ids is not None:
        for chat_id in chat_ids:
            try:
                admins = await bot.get_chat_administrators(chat_id=chat_id, request_timeout=10)
                new_admins = list(
                    map(lambda a: UserChat(user_tg_id=a.user.id, chat_tg_id=chat_id, isAdmin=True), admins))

                new_admin_ids = list(map(lambda x: x.user_tg_id, new_admins))
                old_admins: list[UserChat] = await user_repo.find_admins_by_chat_id(chat_id=chat_id)
                for old_admin in old_admins:
                    if old_admin.user_tg_id not in new_admin_ids:
                        print(f'user id: {old_admin.user_tg_id}, isAdmin: {old_admin.isAdmin}')
                        new_admins.append(
                            UserChat(user_tg_id=old_admin.user_tg_id, chat_tg_id=old_admin.chat_tg_id, isAdmin=False))

                await user_repo.update_or_insert_all(new_admins)
            except TelegramBadRequest as ex:
                logger.error(f'Exception get_chat_administrators: {ex.message}')
                pass

    await user_repo.session.close()

    logger.info("Completed updating the list of administrators after a reboot")
