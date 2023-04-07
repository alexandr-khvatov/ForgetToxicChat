from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import SmallInteger
from sqlalchemy import VARCHAR

from .base import Base


class Chat(Base):
    __tablename__ = "chat"

    chat_tg_id = Column(BigInteger, primary_key=True, index=True)
    mode = Column(VARCHAR, default='mute')
    mute_time = Column(SmallInteger, default=5)
    num_warnings = Column(SmallInteger, default=5)
