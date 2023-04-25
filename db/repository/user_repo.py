import logging

from pydantic import parse_obj_as
from sqlalchemy import select, and_, exc, delete
from sqlalchemy.exc import SQLAlchemyError

from config.config import config
from db.models.userchat import UserChat
from db.repository._base import SQLAlchemyRepo

logger = logging.getLogger(__name__)


class UserRepo(SQLAlchemyRepo):

    async def get_all_chat_when_bot_admin(self, user_id):
        stmt = select(UserChat.chat_tg_id) \
            .where(UserChat.user_tg_id == user_id) \
            .where(UserChat.isAdmin == True)
        _ = await self.session.execute(stmt)
        return _.scalars().all()

    async def find_user(self, user_id, chat_id):
        stmt = select(UserChat) \
            .where(UserChat.user_tg_id == user_id) \
            .where(UserChat.chat_tg_id == chat_id)
        _ = await self.session.execute(stmt)
        user = _.scalars().first()
        if user:
            return user
        else:
            self.session.add(UserChat(user_tg_id=user_id, chat_tg_id=chat_id))
            await self.session.commit()
            return await self.find_user(user_id=user_id, chat_id=chat_id)

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
        await self.session.close()
        return res is not None

    async def update_or_insert(self, user: UserChat):
        stmt = select(UserChat) \
            .where(UserChat.user_tg_id == user.user_tg_id) \
            .where(UserChat.chat_tg_id == user.chat_tg_id)
        _ = await self.session.execute(stmt)
        exist_user: UserChat = _.scalars().first()
        if exist_user is not None:
            exist_user.isAdmin = user.isAdmin
            await self.session.commit()
        else:
            self.session.add(user)
            await self.session.commit()

    async def update_or_insert_all(self, users: list[UserChat]):
        for user in users:
            await self.update_or_insert(user)

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

    async def rating_increment(self, user_id, chat_id):
        stmt = select(UserChat).where(UserChat.user_tg_id == user_id).where(UserChat.chat_tg_id == chat_id)
        user: UserChat = (await self.session.execute(stmt)).scalars().first()
        if user:
            current_num_warnings = user.num_warnings
            new_rating = current_num_warnings + 1
            user.num_warnings = new_rating
            try:
                # self.session.add(chat)
                await self.session.commit()
                return user
            except SQLAlchemyError:
                msg_err = "Error update rating user with id:{%s} in chat with id:{%s})"
                logger.error(msg_err)
                await self.session.rollback()
                raise
        else:
            user = UserChat(user_tg_id=user_id, chat_tg_id=chat_id)
            await self.add(user)
            return user

    async def rating_reset(self, user_id, chat_id):
        stmt = select(UserChat).where(UserChat.user_tg_id == user_id).where(UserChat.chat_tg_id == chat_id)
        user: UserChat = (await self.session.execute(stmt)).scalars().first()
        if user:
            user.num_warnings = 0
            try:
                # self.session.add(chat)
                await self.session.commit()
                return user
            except SQLAlchemyError:
                msg_err = "Error update rating user with id:{%s} in chat with id:{%s})"
                logger.error(msg_err)
                await self.session.rollback()
                raise
        else:
            user = UserChat(user_tg_id=user_id, chat_tg_id=chat_id)
            await self.add(user)
            return user
