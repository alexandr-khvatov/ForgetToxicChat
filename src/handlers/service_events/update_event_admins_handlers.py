import asyncio
import logging

from aiogram import types, Router, Bot
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, KICKED, LEFT, \
    RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR, IS_NOT_MEMBER
from aiogram.types import ChatMemberUpdated

from src.db.models.userchat import UserChat
from src.db.repository.user_repo import UserRepo

router = Router()
logger = logging.getLogger(__name__)

chats_variants = {
    "group": "группу",
    "supergroup": "супергруппу"
}


@router.chat_member(
    ChatMemberUpdatedFilter(member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) >> (ADMINISTRATOR | CREATOR)))
async def admin_added(event: types.ChatMemberUpdated, user_repo: UserRepo):
    logger.debug('Add_admin:')
    new = event.new_chat_member
    chat = event.chat
    logger.debug(
        f'Admin rights granted to the user: {new.user.id}  {new.user.username} in chat: {chat.id} {chat.username}')
    await user_repo.update_or_insert(UserChat(user_tg_id=new.user.id, chat_tg_id=chat.id, isAdmin=True))
    logger.debug(
        f'add admin to db: Admin rights granted to the user: {new.user.id}  {new.user.username} in chat: {chat.id} {chat.username}')


@router.chat_member(
    ChatMemberUpdatedFilter(member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) << (ADMINISTRATOR | CREATOR)))
async def admin_removed(event: types.ChatMemberUpdated, user_repo: UserRepo):
    logger.debug('Removed_admin:')
    user = event.new_chat_member.user
    chat = event.chat
    await user_repo.update_or_insert(UserChat(user_tg_id=user.id, chat_tg_id=chat.id, isAdmin=False))
    logger.debug(f'Remove admin with id:{user.id} username:{user.username}  chat: {chat.id} {chat.username}')


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> ADMINISTRATOR))
async def bot_added_as_admin(event: ChatMemberUpdated, bot: Bot):
    # bot added as admin
    delete_message_after = await bot.send_message(
        chat_id=event.chat.id,
        text=f"Привет! Спасибо, что добавили меня в "
             f'{chats_variants[event.chat.type]} "{event.chat.title}" '
             f"как администратора. ID чата: {event.chat.id}"
    )

    await asyncio.sleep(10)
    await delete_message_after.delete()


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> MEMBER))
async def bot_added_as_member(event: ChatMemberUpdated, bot: Bot):
    # bot added as a member
    chat_info = await bot.get_chat(event.chat.id)
    if chat_info.permissions.can_send_messages:
        delete_message_after = await bot.send_message(
            chat_id=event.chat.id,
            text=f"Привет! Спасибо, что добавили меня в "
                 f'{chats_variants[event.chat.type]} "{event.chat.title}" '
                 f"Дайте мне права админа, чтобы я мог модерировать. ID чата: {event.chat.id}"
        )
        await asyncio.sleep(10)
        await delete_message_after.delete()


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) >> (ADMINISTRATOR | CREATOR)))
async def bot_promoted_to_administrator(event: ChatMemberUpdated, user_repo: UserRepo, bot: Bot):
    logger.debug("bot_promoted_to_administrator")
    chat_id = event.chat.id
    admins = await bot.get_chat_administrators(chat_id=chat_id)
    admin_models = list(map(lambda a: UserChat(user_tg_id=a.user.id, chat_tg_id=chat_id, isAdmin=True), admins))
    await user_repo.update_or_insert_all(admin_models)
    await user_repo.update_or_insert(UserChat(user_tg_id=bot.id, chat_tg_id=chat_id, isAdmin=True))


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) << (ADMINISTRATOR | CREATOR)))
async def bot_promoted_to_administrator(event: ChatMemberUpdated, user_repo: UserRepo, bot: Bot):
    logger.debug("bot removed from admins")
    chat_id = event.chat.id
    await user_repo.update_or_insert(UserChat(user_tg_id=bot.id, chat_tg_id=chat_id, isAdmin=False))
