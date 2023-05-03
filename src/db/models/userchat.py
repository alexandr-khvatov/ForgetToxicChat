import datetime

from sqlalchemy import BigInteger, DateTime
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer

from .base import Base


class UserChat(Base):
    __tablename__ = "user_chat"

    user_tg_id = Column(BigInteger, primary_key=True, index=True)
    chat_tg_id = Column(BigInteger, primary_key=True, index=True)
    num_warnings = Column(Integer, default=0)
    total_warnings = Column(Integer, default=0)
    message_counter = Column(BigInteger, default=0)
    isAdmin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)



