import logging

from sqlalchemy import exc, select
from sqlalchemy.exc import SQLAlchemyError

from src.db.models.chat_message import ChatMessage
from src.db.repository._base import SQLAlchemyRepo

logger = logging.getLogger(__name__)


class ChatMessageRepo(SQLAlchemyRepo):

    async def add(self, chat_msg: ChatMessage):
        try:
            self.session.add(chat_msg)
            await self.session.commit()
        except exc.SQLAlchemyError:
            msg_err = f"Error add chat_msg with params: ( chat_id:{chat_msg.chat_tg_id}, user_id:{chat_msg.user_tg_id})"
            logger.error(msg_err)
            await self.session.rollback()
            raise

    async def mark_msg_as_toxic(self, user_id, chat_id, msg_id):
        logger.debug("update")
        stmt = select(ChatMessage).where(ChatMessage.user_tg_id == user_id).where(
            ChatMessage.chat_tg_id == chat_id).where(ChatMessage.message_id == msg_id)
        msg: ChatMessage = (await self.session.execute(stmt)).scalars().first()
        if msg:
            msg.isToxic = True

            try:
                # self.session.add(chat)
                await self.session.commit()
                return msg
            except SQLAlchemyError:
                msg_err = f"Error mark msg as toxic: user_id:{user_id}  chat_id:{chat_id},message_id:{msg_id})"
                logger.error(msg_err)
                await self.session.rollback()
                raise
