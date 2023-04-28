import datetime

from sqlalchemy import BigInteger, DateTime, Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import TEXT

from .base import Base


class ChatMessage(Base):
    __tablename__ = "chat_message"

    user_tg_id = Column(BigInteger, primary_key=True, index=True)
    chat_tg_id = Column(BigInteger, primary_key=True, index=True)
    message_id = Column(BigInteger, primary_key=True, index=True)
    message_text = Column(TEXT)
    message_len = Column(Integer)
    isToxic = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

#  alembic revision --autogenerate -m 'alter table user_chat add total_warning'
# alembic upgrade edb8bf3f7ca7
