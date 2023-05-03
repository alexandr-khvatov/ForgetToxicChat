import logging

from pydantic import parse_obj_as
from sqlalchemy import select, and_, exc, delete, func
from sqlalchemy.exc import SQLAlchemyError

from src.config.config import config
from src.db.models.userchat import UserChat
from src.db.repository._base import SQLAlchemyRepo

logger = logging.getLogger(__name__)


class UserRepo(SQLAlchemyRepo):

    async def get_all_chat_when_bot_admin(self, user_id):
        logger.debug("get_all_chat_when_bot_admin")
        stmt = select(UserChat.chat_tg_id) \
            .where(UserChat.user_tg_id == user_id) \
            .where(UserChat.isAdmin == True)
        _ = await self.session.execute(stmt)
        return _.scalars().all()

    async def find_user(self, user_id, chat_id):
        logger.debug("find_user")
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

    async def find_admins_by_chat_id(self, chat_id):
        stmt = select(UserChat) \
            .where(and_(UserChat.isAdmin == True, UserChat.chat_tg_id == chat_id)) \
            .limit(config.tg_bot.max_admins_count)
        _ = await self.session.execute(stmt)
        return _.scalars().all()

    async def is_admin(self, user_id: int, chat_id: int):
        logger.debug("is_admin")
        stmt = select(UserChat.user_tg_id).filter(
            and_(
                UserChat.user_tg_id == user_id,
                UserChat.chat_tg_id == chat_id,
                UserChat.isAdmin == True, ))
        res = (await self.session.execute(stmt)).first()
        await self.session.close()
        return res is not None

    async def update_or_insert(self, user: UserChat):
        logger.debug("update_or_insert")
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
        logger.debug("update_or_insert_all")
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
        logger.debug("add_all")
        try:
            self.session.add_all(users)
            await self.session.commit()
        except exc.SQLAlchemyError:
            msg_err = f"Error remove admins by chat id and user ids with params: {UserChat}"
            logger.error(msg_err)
            await self.session.rollback()
            raise

    async def remove_users_by_chat_id(self, chat_id, user_ids):
        logger.debug("remove_users_by_chat_id")
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
        logger.debug("rating_increment")
        stmt = select(UserChat).where(UserChat.user_tg_id == user_id).where(UserChat.chat_tg_id == chat_id)
        user: UserChat = (await self.session.execute(stmt)).scalars().first()
        if user:
            current_num_warnings = user.num_warnings
            current_total_warnings = user.total_warnings
            new_rating = current_num_warnings + 1
            new_total_rating = current_total_warnings + 1
            user.num_warnings = new_rating
            user.total_warnings = new_total_rating
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
        logger.debug("rating_reset")
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

    async def get_chat_warnings_active(self, chat_id):
        logger.debug("get_chat_warnings_active")
        stmt = select(func.sum(UserChat.num_warnings)).where(UserChat.chat_tg_id == chat_id)
        _ = await self.session.execute(stmt)
        num_warnings_activ = _.scalars().first()
        logger.debug('chat with id: {%s}, num_warnings_activ: {%s}', chat_id, num_warnings_activ)
        return num_warnings_activ if num_warnings_activ is not None else 0

    async def get_chat_warnings_total(self, chat_id):
        logger.debug("get_chat_warnings_total")
        stmt = select(func.sum(UserChat.total_warnings)).where(UserChat.chat_tg_id == chat_id)
        _ = await self.session.execute(stmt)
        num_warnings_total = _.scalars().first()
        logger.debug('chat with id: {%s}, num_warnings_total: {%s}', chat_id, num_warnings_total)
        return num_warnings_total if num_warnings_total is not None else 0

    async def get_chat_num_messages_for_user(self, user_id, chat_id):
        logger.debug("get_chat_num_messages_for_user")
        stmt = select(UserChat.message_counter).where(UserChat.user_tg_id == user_id).where(
            UserChat.chat_tg_id == chat_id)
        _ = await self.session.execute(stmt)
        num_chat_messages_for_user = _.scalars().first()
        logger.debug('user with id {} in chat with id: {%s} send num_chat_messages_for_user: {%s}', user_id, chat_id,
                     num_chat_messages_for_user)
        return num_chat_messages_for_user if num_chat_messages_for_user is not None else 0

    async def get_chat_num_messages(self, chat_id):
        logger.debug("get_chat_num_messages")
        stmt = select(func.sum(UserChat.message_counter)).where(UserChat.chat_tg_id == chat_id)
        _ = await self.session.execute(stmt)
        num_chat_messages = _.scalars().first()
        logger.debug('user sends in chat with id: {%s} total num_chat_messages: {%s}', chat_id,
                     num_chat_messages)
        return num_chat_messages if num_chat_messages is not None else 0

    async def messages_increment(self, user_id, chat_id):
        logger.debug("num_messages_increment")
        stmt = select(UserChat).where(UserChat.user_tg_id == user_id).where(
            UserChat.chat_tg_id == chat_id)
        user_chat: UserChat = (await self.session.execute(stmt)).scalars().first()
        if user_chat:
            user_chat.message_counter = user_chat.message_counter + 1
            try:
                await self.session.commit()
                return user_chat
            except SQLAlchemyError:
                msg_err = "Error num_messages_increment user_chat with id:{%s})"
                logger.error(msg_err, chat_id)
                await self.session.rollback()
                raise
        else:
            user_chat = UserChat(user_tg_id=user_id, chat_tg_id=chat_id, message_counter=1)
            await self.add(user_chat)
            return user_chat
