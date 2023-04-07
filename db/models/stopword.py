from sqlalchemy import BigInteger, func
from sqlalchemy import Column
from sqlalchemy import VARCHAR
from sqlalchemy import DateTime

from .base import Base


class StopWord(Base):
    __tablename__ = "stop_word"

    chat_tg_id = Column(BigInteger, primary_key=True, index=True)
    stop_word = Column(VARCHAR, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())
