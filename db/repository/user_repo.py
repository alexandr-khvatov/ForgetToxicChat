import logging

from pydantic import parse_obj_as
from sqlalchemy import select, and_, exc, delete

from config.config import config
from db.models.userchat import UserChat
from db.repository._base import SQLAlchemyRepo

logger = logging.getLogger(__name__)


class UserRepo(SQLAlchemyRepo):

    async def find_admin_ids_by_chat_id(self, chat_id):
        stmt = select(UserChat.user_tg_id) \
            .where(and_(UserChat.isAdmin == True, UserChat.chat_tg_id == chat_id)) \
            .limit(config.tg_bot.max_admins_count)
        _ = await self.session.execute(stmt)
        return parse_obj_as(list[int], _.scalars().all())

    async def is_admin(self, user_id: int, chat_id: int):
        stmt = select(UserChat.user_tg_id).filter(
            and_(
                UserChat.user_tg_id == user_id,
                UserChat.chat_tg_id == chat_id,
                UserChat.isAdmin == True, ))
        res = (await self.session.execute(stmt)).first()
        return res is not None

    async def add(self, user: UserChat):
        try:
            self.session.add(user)
            await self.session.commit()
        except exc.SQLAlchemyError:
            msg_err = f"Error add user with params: ( chat_id:{user.chat_tg_id}, user_id:{user.user_tg_id})"
            logger.error(msg_err)
            await self.session.rollback()
            raise

    async def add_all(self, users: list[UserChat]):
        try:
            self.session.add_all(users)
            await self.session.commit()
        except exc.SQLAlchemyError:
            msg_err = f"Error remove admins by chat id and user ids with params: {UserChat}"
            logger.error(msg_err)
            await self.session.rollback()
            raise

    async def remove_users_by_chat_id(self, chat_id, user_ids):
        stmt = (
            delete(UserChat).where(and_(UserChat.user_tg_id.in_(user_ids),
                                        UserChat.chat_tg_id == chat_id))
        )
        try:
            await self.session.execute(statement=stmt)
            await self.session.commit()
        except exc.SQLAlchemyError:
            msg_err = f"Error remove admins by chat id and user ids with params: ( chat_id:{chat_id}, user_id:{user_ids})"
            logger.error(msg_err)
            await self.session.rollback()
            raise
