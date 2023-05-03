import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy import Column
from sqlalchemy import SmallInteger
from sqlalchemy import VARCHAR

from .base import Base
from .chat_mode_restriction import Mode


class Chat(Base):
    __tablename__ = "chat"

    chat_tg_id = Column(BigInteger, primary_key=True, index=True)
    mode = Column(VARCHAR, default=Mode.remove.name)
    mute_time = Column(SmallInteger, default=300)
    num_warnings = Column(SmallInteger, default=5)
    message_counter = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
