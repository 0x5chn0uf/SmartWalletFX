from __future__ import annotations

from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import Settings


class DatabaseService:
    """Create database engines and session factories for DI."""

    def __init__(self, settings: Settings) -> None:
        self.__settings = settings
        self._setup_engines()
        self._setup_session_factories()

    def _setup_engines(self) -> None:
        db_url = self.__settings.DATABASE_URL
        if db_url.startswith("sqlite:///") and "+aiosqlite" not in db_url:
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        self.async_engine = create_async_engine(db_url)

        sync_url = self.__settings.DATABASE_URL
        if "+aiosqlite" in sync_url:
            sync_url = sync_url.replace("+aiosqlite", "")
        elif "+asyncpg" in sync_url:
            sync_url = sync_url.replace("+asyncpg", "")
        self.sync_engine = create_engine(sync_url)

    def _setup_session_factories(self) -> None:
        self.async_session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self.sync_session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.sync_engine,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        async with self.async_session_factory() as session:
            yield session

    def get_sync_session(self) -> sessionmaker:
        return self.sync_session_factory()

    Base = declarative_base()
