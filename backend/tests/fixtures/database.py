"""Database fixtures for the test suite."""

import pytest
import pytest_asyncio
import sqlalchemy as _sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.core.config import ConfigurationService
from app.core.database import DatabaseService


@pytest.fixture(scope="session")
def config_service():
    """Configuration service for tests."""
    return ConfigurationService()


@pytest.fixture(scope="session")
def database_service(config_service):
    """Database service for tests."""
    return DatabaseService(config_service)


@pytest_asyncio.fixture
async def db_session(database_service):
    """
    Function-scoped async session using the session-scoped async engine.
    Provides complete test isolation with automatic rollback.
    """
    async_session = async_sessionmaker(
        bind=database_service.async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture(scope="module")
async def module_db_session(database_service):
    """
    Module-scoped async session for shared test data.
    Use this when you need to share database state across multiple tests in a module.
    """
    async_session = async_sessionmaker(
        bind=database_service.async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def sync_session(database_service):
    """
    Function-scoped sync session using the session-scoped sync engine.
    Provides complete test isolation with automatic rollback.
    """
    Session = sessionmaker(
        bind=database_service.sync_engine, autocommit=False, autoflush=False
    )
    session = Session()
    transaction = session.begin()
    try:
        yield session
    finally:
        if transaction.is_active:
            transaction.rollback()
        session.close()


@pytest.fixture(scope="module")
def module_sync_session(database_service):
    """
    Module-scoped sync session for shared test data.
    Use this when you need to share database state across multiple tests in a module.
    """
    Session = sessionmaker(
        bind=database_service.sync_engine, autocommit=False, autoflush=False
    )
    session = Session()
    transaction = session.begin()
    try:
        yield session
    finally:
        if transaction.is_active:
            transaction.rollback()
        session.close()


@pytest_asyncio.fixture
async def clean_db_session(database_service):
    """
    Function-scoped async session with automatic cleanup.
    Ensures the database is clean before and after each test.
    """
    async_session = async_sessionmaker(
        bind=database_service.async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Start transaction
        await session.begin()

        # Clean up any existing data
        insp = _sa.inspect(database_service.async_engine)
        for table in reversed(insp.get_table_names()):
            await session.execute(_sa.text(f"DELETE FROM {table}"))

        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def clean_sync_session(database_service):
    """
    Function-scoped sync session with automatic cleanup.
    Ensures the database is clean before and after each test.
    """
    Session = sessionmaker(
        bind=database_service.sync_engine, autocommit=False, autoflush=False
    )
    session = Session()
    transaction = session.begin()

    # Clean up any existing data
    insp_sync = _sa.inspect(database_service.sync_engine)
    for table in reversed(insp_sync.get_table_names()):
        session.execute(_sa.text(f"DELETE FROM {table}"))

    try:
        yield session
    finally:
        if transaction.is_active:
            transaction.rollback()
        session.close()
