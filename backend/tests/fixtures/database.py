"""Database fixtures for the test suite."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker


@pytest_asyncio.fixture
async def db_session():
    """
    Function-scoped async session using the session-scoped async engine.
    Provides complete test isolation with automatic rollback.
    """
    from app.core.database import engine

    async_session = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture(scope="module")
async def module_db_session():
    """
    Module-scoped async session for shared test data.
    Use this when you need to share database state across multiple tests in a module.
    """
    from app.core.database import engine

    async_session = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def sync_session():
    """
    Function-scoped sync session using the session-scoped sync engine.
    Provides complete test isolation with automatic rollback.
    """
    from app.core.database import sync_engine

    Session = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
    session = Session()
    transaction = session.begin()
    try:
        yield session
    finally:
        if transaction.is_active:
            transaction.rollback()
        session.close()


@pytest.fixture(scope="module")
def module_sync_session():
    """
    Module-scoped sync session for shared test data.
    Use this when you need to share database state across multiple tests in a module.
    """
    from app.core.database import sync_engine

    Session = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
    session = Session()
    transaction = session.begin()
    try:
        yield session
    finally:
        if transaction.is_active:
            transaction.rollback()
        session.close()


@pytest_asyncio.fixture
async def clean_db_session():
    """
    Function-scoped async session with automatic cleanup.
    Ensures the database is clean before and after each test.
    """
    from app.core.database import engine

    async_session = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Start transaction
        await session.begin()

        # Clean up any existing data
        for table in reversed(engine.table_names()):
            await session.execute(f"DELETE FROM {table}")

        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def clean_sync_session():
    """
    Function-scoped sync session with automatic cleanup.
    Ensures the database is clean before and after each test.
    """
    from app.core.database import sync_engine

    Session = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
    session = Session()
    transaction = session.begin()

    # Clean up any existing data
    for table in reversed(sync_engine.table_names()):
        session.execute(f"DELETE FROM {table}")

    try:
        yield session
    finally:
        if transaction.is_active:
            transaction.rollback()
        session.close()
