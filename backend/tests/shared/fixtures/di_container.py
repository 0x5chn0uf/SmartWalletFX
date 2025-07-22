"""
Dependency Injection Container fixtures for testing.

This module provides fixtures for testing components that use the new
dependency injection pattern with singleton services.
"""

from contextlib import asynccontextmanager
from unittest.mock import Mock

import httpx
import pytest
import pytest_asyncio

from app.core.database import CoreDatabase
from app.di import DIContainer

# === DI CONTAINER FIXTURES ===


@pytest.fixture
def test_di_container_with_db(db_session):
    """Create a DIContainer with database session override for testing."""
    di_container = DIContainer()

    # Override the database service to use the test session
    mock_database = Mock(spec=CoreDatabase)

    @asynccontextmanager
    async def mock_get_session():
        yield db_session

    mock_database.get_session = mock_get_session
    mock_database.async_engine = Mock()
    mock_database.sync_engine = Mock()

    di_container.register_core("database", mock_database)

    return di_container


@pytest.fixture
def test_app_with_di_container(test_di_container_with_db):
    """Create a FastAPI app using DIContainer for integration testing."""
    from app.main import ApplicationFactory

    # Create app using DIContainer
    app_factory = ApplicationFactory(test_di_container_with_db)
    app = app_factory.create_app()

    return app


@pytest_asyncio.fixture
async def integration_async_client(test_app_with_di_container):
    """Create an async test client using DIContainer for integration tests."""
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as ac:
        yield ac
