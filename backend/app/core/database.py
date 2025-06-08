from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///')

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()

# Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session
