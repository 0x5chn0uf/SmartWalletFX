"""Database fixtures for the test suite."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Configuration
from app.core.database import CoreDatabase

# Import all models to ensure they are registered with Base before create_all
from app.models import *  # noqa: F401, F403


@pytest.fixture(scope="session")
def config():
    """Configuration service for tests."""
    from .test_config import UnitTestConfiguration

    return UnitTestConfiguration()


@pytest_asyncio.fixture
async def database(config):
    """Database service for tests."""
    import os

    from app.utils.logging import Audit

    audit = Audit()

    # For integration tests, use a file-based database to avoid connection issues
    if hasattr(config, "DATABASE_URL") and "memory" in config.DATABASE_URL:
        # Create a temporary test-specific configuration with file-based database
        from tests.shared.fixtures.test_config import (
            create_integration_test_config,
        )

        test_db_path = "./test_integration.db"

        # Clean up any existing test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

        file_config = create_integration_test_config(
            f"sqlite+aiosqlite:///{test_db_path}"
        )
        db = CoreDatabase(file_config, audit)
    else:
        db = CoreDatabase(config, audit)

    # Initialize database schema for tests
    await db.init_db()
    return db


@pytest_asyncio.fixture
async def db_session(database):
    """
    Function-scoped async session using the session-scoped async engine.
    For integration tests, commits changes. For unit tests, uses transactions.
    """
    import os

    # Ensure test database file permissions are correct if it exists
    if os.path.exists("test.db"):
        try:
            # Make sure the database file is writable
            os.chmod("test.db", 0o666)
        except (OSError, PermissionError):
            # If we can't change permissions, remove the file and let SQLAlchemy recreate it
            try:
                os.remove("test.db")
            except (OSError, PermissionError):
                pass  # If we can't remove it, let init_db() handle the error

    # Initialize database tables before creating sessions
    await database.init_db()

    async_session = async_sessionmaker(
        bind=database.async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Don't start a transaction - let each operation commit individually
        # This allows integration tests to persist data between operations
        yield session
