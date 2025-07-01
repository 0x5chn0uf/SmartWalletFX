"""FastAPI TestClient fixtures for the test suite."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.database import get_db


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


@pytest_asyncio.fixture
async def client_with_db(test_app, db_session):
    """
    Test client with database session dependency override.
    Useful for testing endpoints that require database access.
    """

    async def _override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = _override_get_db

    client = TestClient(test_app)
    yield client

    # Clean up dependency override
    test_app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def async_client_with_db(test_app, db_session):
    """
    Async test client with database session dependency override.
    Useful for testing async endpoints that require database access.
    """

    async def _override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac

    # Clean up dependency override
    test_app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def authenticated_client(test_app, test_user, db_session):
    """
    Test client with authentication and user context.
    Provides a fully configured client for testing authenticated endpoints.
    """
    from app.utils.jwt import JWTUtils

    async def _override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = _override_get_db

    access_token = JWTUtils.create_access_token(
        str(test_user.id),
        additional_claims={
            "email": test_user.email,
            "roles": test_user.roles
            if getattr(test_user, "roles", None)
            else ["individual_investor"],
            "attributes": {},
        },
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    client = TestClient(test_app, headers=headers)
    yield client

    # Clean up dependency override
    test_app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def authenticated_async_client(test_app, test_user, db_session):
    """
    Async test client with authentication and user context.
    Provides a fully configured async client for testing authenticated endpoints.
    """
    from app.utils.jwt import JWTUtils

    async def _override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = _override_get_db

    access_token = JWTUtils.create_access_token(
        str(test_user.id),
        additional_claims={
            "email": test_user.email,
            "roles": test_user.roles
            if getattr(test_user, "roles", None)
            else ["individual_investor"],
            "attributes": {},
        },
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    async with AsyncClient(app=test_app, base_url="http://test", headers=headers) as ac:
        yield ac

    # Clean up dependency override
    test_app.dependency_overrides.pop(get_db, None)
