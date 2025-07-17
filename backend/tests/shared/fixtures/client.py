"""FastAPI TestClient fixtures for the test suite."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient


async def get_db_for_testing():
    """
    Database dependency for testing that gets the database service from DI container.
    This can be overridden in test fixtures.
    """
    # Local import to avoid circular import
    from app.di import DIContainer

    di_container = DIContainer()
    database = di_container.get_core("database")
    async with database.get_session() as session:
        yield session


@pytest.fixture
def client(test_app):
    """
    Basic test client without authentication.
    Provides a standard FastAPI TestClient for unauthenticated endpoints.
    """
    return TestClient(test_app)


@pytest_asyncio.fixture
async def async_client(test_app):
    """
    Async test client without authentication.
    Provides an AsyncClient for async endpoint testing.
    """
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def client_with_db(test_app, db_session):
    """
    Test client with database session dependency override.
    Useful for testing endpoints that require database access.
    """

    async def _override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db_for_testing] = _override_get_db

    with TestClient(test_app) as client:
        yield client

    test_app.dependency_overrides.pop(get_db_for_testing, None)


@pytest_asyncio.fixture
async def async_client_with_db(test_app, db_session):
    """
    Async test client with database session dependency override.
    Useful for testing async endpoints that require database access.
    """

    async def _override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db_for_testing] = _override_get_db

    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac

    # Clean up dependency override
    test_app.dependency_overrides.pop(get_db_for_testing, None)
