from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Boolean

from .base import Base


class UserChat(Base):
    __tablename__ = "user_chat"

    user_tg_id = Column(BigInteger, primary_key=True, index=True)
    chat_tg_id = Column(BigInteger, primary_key=True, index=True)
    mute_time = Column(Integer, default=0)
    isAdmin = Column(Boolean, default=False)
