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
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.database import CoreDatabase
from app.di import DIContainer

# === DI CONTAINER FIXTURES ===


@pytest.fixture
def mock_di_container():
    """Mock DIContainer for testing."""
    mock = Mock()
    mock.get_core = Mock()
    mock.get_repository = Mock()
    mock.get_usecase = Mock()
    mock.get_endpoint = Mock()
    mock.register_core = Mock()
    mock.register_repository = Mock()
    mock.register_usecase = Mock()
    mock.register_endpoint = Mock()
    return mock


@pytest.fixture
def test_di_container():
    """Create a real DIContainer instance for testing."""
    return DIContainer()


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


@pytest.fixture
def integration_client(test_app_with_di_container):
    """Create a synchronous test client using DIContainer for integration tests."""
    return TestClient(test_app_with_di_container)


@pytest_asyncio.fixture
async def integration_async_client(test_app_with_di_container):
    """Create an async test client using DIContainer for integration tests."""
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_integration_client(
    test_app_with_di_container, test_user, test_di_container_with_db
):
    """Create an authenticated async test client using DIContainer."""
    # Get JWTUtils from DI container
    jwt_utils = test_di_container_with_db.get_utility("jwt_utils")

    # Create access token for test user
    access_token = jwt_utils.create_access_token(
        subject=str(test_user.id),
        additional_claims={
            "email": test_user.email,
            "roles": getattr(test_user, "roles", ["individual_investor"]),
            "attributes": {},
        },
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    async with AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as client:
        yield client
