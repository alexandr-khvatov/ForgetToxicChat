import logging

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from config.config import config
from db.models.stopword import StopWord
from db.repository._base import SQLAlchemyRepo

logger = logging.getLogger(__name__)


class StopWordRepo(SQLAlchemyRepo):

    async def find_stop_words_by_chat(self, chat_id):
        stmt = select(StopWord.stop_word) \
            .where(StopWord.chat_tg_id == chat_id) \
            .limit(config.tg_bot.max_stop_word_count)
        _ = await self.session.execute(stmt)
        return _.scalars().all()

    async def get_all(self, chat_id, offset=0, limit=10):
        count = await self.session.scalar(select(func.count()).select_from(
            select(StopWord.chat_tg_id).where(StopWord.chat_tg_id == chat_id).subquery()))
        stmt = select(StopWord.stop_word) \
            .where(StopWord.chat_tg_id == chat_id) \
            .order_by(StopWord.created_at) \
            .limit(limit) \
            .offset(offset)
        _ = await self.session.execute(stmt)
        items = _.scalars().all()
        return count, items

    async def get_counts(self, chat_id):
        stmt = select(func.count()).select_from(
            select(StopWord.chat_tg_id).where(StopWord.chat_tg_id == chat_id).subquery())
        _ = await self.session.execute(stmt)
        return _.scalar_one()

    async def add_all(self, chat_id, bad_words):
        candidate = set(bad_words)
        print(f'candidate:{candidate}')
        current_bws = await self.find_stop_words_by_chat(chat_id)
        print(f'current_bws:{current_bws}')
        if len(current_bws) > 0:
            candidate = candidate - set(current_bws)
            print(f'candidate_next:{candidate}')
        try:
            self.session.add_all(list(map(lambda x: StopWord(chat_tg_id=chat_id, stop_word=x), candidate)))
            await self.session.commit()
        except SQLAlchemyError as ex:
            msg_err = f"Error add_all bad words chat with id:{chat_id}:, ex:{ex}"
            logger.error(msg_err)
            await self.session.rollback()
            raise
