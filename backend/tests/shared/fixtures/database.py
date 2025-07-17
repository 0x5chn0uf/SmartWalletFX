"""Database fixtures for the test suite."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import ConfigurationService
from app.core.database import CoreDatabase


@pytest.fixture(scope="session")
def config_service():
    """Configuration service for tests."""
    return ConfigurationService()


@pytest.fixture(scope="session")
def database(config_service):
    """Database service for tests."""
    from app.utils.logging import Audit

    audit = Audit()
    return CoreDatabase(config_service, audit)


@pytest_asyncio.fixture
async def db_session(database):
    """
    Function-scoped async session using the session-scoped async engine.
    Provides complete test isolation with automatic rollback.
    """
    async_session = async_sessionmaker(
        bind=database.async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()
