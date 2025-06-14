# Synchronous SQLAlchemy imports for Celery / legacy callers
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker  # type: ignore
from sqlalchemy.orm import declarative_base

from app.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///") and "+aiosqlite" not in db_url:
    db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
SQLALCHEMY_DATABASE_URL = db_url

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
)
SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

Base = declarative_base()

# ---------------------------------------------------------------------------
# Synchronous engine/session for Celery tasks or scripts that cannot use async
# ---------------------------------------------------------------------------

sync_db_url = settings.DATABASE_URL.replace("+aiosqlite", "")
sync_engine = create_engine(
    sync_db_url,
    connect_args={"check_same_thread": False} if "sqlite" in sync_db_url else {},
)

# Regular session factory
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


# Dependency
async def get_db():
    """
    Dependency that provides an async database session.
    Yields:
        AsyncSession: An async SQLAlchemy session for database operations.
    """
    async with SessionLocal() as session:
        yield session
