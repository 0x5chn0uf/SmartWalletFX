# Synchronous SQLAlchemy imports for Celery / legacy callers
from contextlib import asynccontextmanager

from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker  # type: ignore
from sqlalchemy.orm import declarative_base

from app.core.config import Configuration
from app.utils.logging import Audit


class CoreDatabase:
    """Database service managing database connections and sessions."""

    def __init__(self, config: Configuration, audit: Audit):
        self.config = config
        self._setup_async_engine()
        self._setup_sync_engine()
        self._setup_session_factories()
        self.audit = audit

    def _setup_async_engine(self):
        """Set up the async database engine."""
        db_url = self.config.DATABASE_URL

        # Handle async drivers for different database types
        if db_url.startswith("sqlite:///") and "+aiosqlite" not in db_url:
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

        # Create async engine connection args
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

        # For Postgres we tune the pool size based on settings; SQLite keeps default
        pool_kwargs = {}
        if "postgresql" in str(db_url):
            pool_kwargs = {
                "pool_size": self.config.DB_POOL_SIZE,
                "max_overflow": self.config.DB_MAX_OVERFLOW,
            }

        self.async_engine = create_async_engine(
            db_url,
            connect_args=connect_args,
            **pool_kwargs,  # type: ignore[arg-type]
        )

    def _setup_sync_engine(self):
        """Set up the sync database engine for Celery tasks."""
        sync_db_url = self.config.DATABASE_URL

        # Convert async drivers back to sync for synchronous operations
        if "+aiosqlite" in sync_db_url:
            sync_db_url = sync_db_url.replace("+aiosqlite", "")
        elif "+asyncpg" in sync_db_url:
            sync_db_url = sync_db_url.replace("+asyncpg", "")

        self.sync_engine = create_engine(
            sync_db_url,
            connect_args={"check_same_thread": False}
            if "sqlite" in sync_db_url
            else {},
        )

    def _setup_session_factories(self):
        """Set up session factories for both async and sync operations."""
        self.async_session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self.sync_session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self.sync_engine
        )

    async def init_db(self) -> None:
        """
        Initialize the database tables asynchronously.
        Creates all tables defined in the SQLAlchemy models if they do not exist.
        """
        self.audit.info("database_initialization_started")

        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self.audit.info("database_initialization_completed")
        except Exception as e:
            self.audit.error("database_initialization_failed", error=str(e))
            raise

    async def check_database_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            self.audit.error("database_connection_check_failed", error=str(e))
            return False

    @asynccontextmanager
    async def get_session(self):
        """Get an async database session."""
        async with self.async_session_factory() as session:
            yield session

    def get_sync_session(self):
        """Get a sync database session for Celery tasks."""
        return self.sync_session_factory()


# Create declarative base
Base = declarative_base()
