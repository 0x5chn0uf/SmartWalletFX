from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace(
    "sqlite:///", "sqlite+aiosqlite:///"
)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
)
SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

Base = declarative_base()


# Dependency
async def get_db():
    """
    Dependency that provides an async database session.
    Yields:
        AsyncSession: An async SQLAlchemy session for database operations.
    """
    async with SessionLocal() as session:
        yield session
