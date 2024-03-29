import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.db.models.chat import Chat
from src.db.repository._base import SQLAlchemyRepo
from src.filters.callback_data import Action

logger = logging.getLogger(__name__)


class ChatRepo(SQLAlchemyRepo):

    # async def find_chat_settings(self, chat_id):
    #     stmt = select(Chat).where(Chat.chat_tg_id == chat_id)
    #     _ = await self.session.execute(stmt)
    #     return parse_obj_as(Chat, _.first())

    async def find_chat_settings(self, chat_id):
        logger.debug("find_chat_settings")
        stmt = select(Chat).where(Chat.chat_tg_id == chat_id)
        # _ = await self.session.execute(stmt)
        _ = await self.session.execute(stmt)
        chat = _.scalars().first()
        if chat:
            logger.debug('chat with id: {%s} mode {%s} is activ', chat_id, chat.mode)
            return chat
        else:
            self.session.add(Chat(chat_tg_id=chat_id))
            await self.session.commit()
            return await self.find_chat_settings(chat_id=chat_id)

    async def add(self, chat: Chat):
        logger.debug("add")
        try:
            self.session.add(chat)
            await self.session.commit()
        except SQLAlchemyError:
            msg_err = f"Error add chat with id: ( chat_id:{chat.chat_tg_id})"
            logger.error(msg_err)
            await self.session.rollback()
            raise

    async def update(self, chat_id: int, mode: Optional[str] = None, mute_action: Optional[Action] = None,
                     warning_action: Optional[Action] = None):
        logger.debug("update")
        stmt = select(Chat).where(Chat.chat_tg_id == chat_id)
        chat: Chat = (await self.session.execute(stmt)).scalars().first()
        if chat:
            current_num_warnings = chat.num_warnings
            current_mute_time = chat.mute_time
            if mode:
                chat.mode = mode
            if mute_action == Action.mute_minus:
                if current_mute_time > 300:
                    chat.mute_time = current_mute_time - 300
            if mute_action == Action.mute_plus:
                if current_mute_time < 3000:
                    chat.mute_time = current_mute_time + 300
            if warning_action == Action.warning_minus:
                if current_num_warnings > 1:
                    chat.num_warnings = current_num_warnings - 1
            if warning_action == Action.warning_plus:
                if current_num_warnings < 128:
                    chat.num_warnings = current_num_warnings + 1
            try:
                # self.session.add(chat)
                await self.session.commit()
                return chat
            except SQLAlchemyError:
                msg_err = f"Error add chat with id: ( chat_id:{chat.chat_tg_id})"
                logger.error(msg_err)
                await self.session.rollback()
                raise
        else:
            chat = Chat(chat_tg_id=chat_id)
            await self.add(chat)
            return chat

    async def get_chat_num_messages(self, chat_id):
        logger.debug("get_chat_num_messages")
        stmt = select(Chat.message_counter).where(Chat.chat_tg_id == chat_id)
        _ = await self.session.execute(stmt)
        num_chat_messages = _.scalars().first()
        logger.debug('chat with id: {%s}, num_chat_messages: {%s}', chat_id, num_chat_messages)
        return num_chat_messages if num_chat_messages is not None else 0

    async def messages_increment(self, chat_id):
        logger.debug("num_messages_increment")
        stmt = select(Chat).where(Chat.chat_tg_id == chat_id)
        chat: Chat = (await self.session.execute(stmt)).scalars().first()
        if chat:
            chat.message_counter = chat.message_counter + 1
            try:
                await self.session.commit()
                return chat
            except SQLAlchemyError:
                msg_err = "Error num_messages_increment chat with id:{%s})"
                logger.error(msg_err, chat_id)
                await self.session.rollback()
                raise
        else:
            chat = Chat(chat_tg_id=chat_id)
            await self.add(chat)
            return chat
