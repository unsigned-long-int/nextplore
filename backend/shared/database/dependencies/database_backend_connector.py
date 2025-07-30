import os
from typing import AsyncGenerator, Optional, Callable
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = (
            f'postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}'
            f'@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}'
        )

class DatabaseBackendConnector:
    def __init__(self, db_url: Optional[str] = None) -> None:
        self._url = db_url or DATABASE_URL
        self._engine = None
        self._sessionmaker = None
    
    def init(self) -> None:
        if self._engine is None or self._sessionmaker is None:
            self._engine = create_async_engine(
                self._url, 
                echo=False, 
                future=True,
                pool_size=10,
                max_overflow=5,
                pool_timeout=30
            )
            self._sessionmaker = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

    def session_factory(self) -> Callable[[], AsyncSession]:
        if self._sessionmaker is None:
            self.init()
        return self._sessionmaker
    
    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        session_maker = self.session_factory()
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
