from sqlalchemy.ext.asyncio import AsyncSession

# engine = create_async_engine(
#     config.db.build_connection_str(),
#     pool_pre_ping=True
# )
#
# SessionLocal = sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False
# )
from src.db.repository.chat_msg_repo import ChatMessageRepo
from src.db.repository.chat_repo import ChatRepo
from src.db.repository.user_repo import UserRepo


class Database:
    """
    Database class is the highest abstraction level of database and
    can be used in the handlers or any others bot-side functions
    """

    user: UserRepo
    chat: ChatRepo
    msg: ChatMessageRepo

    _session: AsyncSession

    # def __init__(
    #     self, session: AsyncSession, user: UserRepo = None, chat: ChatRepo = None
    # ):
    def __init__(
            self, session: AsyncSession,
            msg: ChatMessageRepo = None,
            chat: ChatRepo = None,
            user: UserRepo = None,
    ):
        self._session = session
        self.msg = msg or ChatMessageRepo(session=session)
        self.chat = chat or ChatRepo(session=session)
        self.user = user or UserRepo(session=session)
