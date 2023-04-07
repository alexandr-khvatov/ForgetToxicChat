import logging

from aiogram import types, Router
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.userchat import UserChat
from db.repository.user_repo import UserRepo
from filters.changing_admins import AdminAdded, AdminRemoved

router = Router()
logger = logging.getLogger(__name__)


@router.chat_member(AdminAdded())
async def admin_added(event: types.ChatMemberUpdated, user_repo: UserRepo):
    new = event.new_chat_member
    chat = event.chat
    await user_repo.add(UserChat(user_tg_id=new.user.id, chat_tg_id=chat.id, isAdmin=True))
    logger.debug(f'Admin rights granted to the user: {new.user.id}  {new.user.username} in chat: {chat.id} {chat.username}')


@router.chat_member(AdminRemoved())
async def admin_removed(event: types.ChatMemberUpdated, user_repo: UserRepo, session: AsyncSession):
    user = event.new_chat_member.user
    chat = event.chat
    await user_repo.remove_users_by_chat_id(chat_id=chat.id, user_ids=[user.id])
    logger.debug(f'Remove admin with id:{user.id} username:{user.username}  chat: {chat.id} {chat.username}')
    # del_stmt = (
    #     delete(UserChat).where(and_(UserChat.chat_tg_id == chat.id, UserChat.user_tg_id == user.id))
    # )
    # await session.execute(del_stmt)
    # print("***********************************")
    # print(chat.id)
    # print(user.id)
    # print("***********************************")
    # await session.commit()
    # # if new.user.id in config.admins.keys():
    # #     del config.admins[new.user.id]
