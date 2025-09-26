from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from config import settings


class EFSDatabase:

    def __init__(self):
        self.engine: AsyncEngine = create_async_engine(
            settings.database_url,
            future=True,
            echo=False,
        )
        self._session = async_sessionmaker(
            self.engine, class_=AsyncSession, pool=NullPool
        )

    @property
    def session(self) -> AsyncSession:
        return self._session()
