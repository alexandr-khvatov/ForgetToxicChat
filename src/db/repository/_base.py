from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyRepo:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session
