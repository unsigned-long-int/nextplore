import os
from uuid import UUID
from typing import AsyncGenerator, Callable, Optional
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = (
            f'postgresql+asyncpg://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}'
            f'@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
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
                pool_size=5,
                max_overflow=5,
                pool_timeout=5,
                pool_recycle=1800,
                pool_pre_ping=True
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
    
    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
    
    @asynccontextmanager
    async def session_scope(
        self, 
        organization_id: Optional[UUID] = None, 
        user_id: Optional[UUID] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        session_maker = self.session_factory()
        async with session_maker() as session:
            try:
                if organization_id is not None:
                    await session.execute(
                        text("SELECT set_config('app.organization_id', :oid, true)"),
                        {'oid': str(organization_id)},
                    )
                if user_id is not None:
                    await session.execute(
                        text("SELECT set_config('app.user_id', :uid, true)"),
                        {'uid': str(user_id)},
                    )
                await session.execute(text("SET LOCAL statement_timeout = '5s'"))
                await session.execute(text("SET LOCAL lock_timeout = '1s'"))

                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
