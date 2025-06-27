"""
Test Fixtures Package

This package provides a comprehensive set of fixtures for testing the application.
The fixtures are organized into modules based on their functionality:

- base.py: Foundation fixtures (engine, app, config)
- database.py: Database-specific fixtures with transactions
- auth.py: Authentication and user fixtures
- client.py: FastAPI TestClient fixtures
- mocks.py: External service mocking fixtures
- config.py: Fixture configuration and settings

Usage:
    # Import specific fixtures
    from tests.fixtures.database import db_session, sync_session
    from tests.fixtures.auth import test_user, authenticated_client
    from tests.fixtures.client import client, async_client
    from tests.fixtures.mocks import mock_redis, mock_web3

    # Use in tests
    async def test_something(db_session, test_user, client):
        # Test implementation
        pass
"""

from .auth import (
    admin_authenticated_client,
    admin_user,
    authenticated_client,
    create_multiple_users,
    create_user_and_wallet,
    create_user_with_tokens,
    inactive_user,
    test_user,
    test_user_with_wallet,
)

# Import all fixtures to make them available
from .base import async_engine, test_app
from .client import (
    async_client,
    async_client_with_db,
    authenticated_async_client,
)
from .client import authenticated_client as client_authenticated
from .client import client, client_with_db
from .config import (
    fixture_config,
    mock_settings,
    test_config,
    test_data_config,
)
from .database import (
    clean_db_session,
    clean_sync_session,
    db_session,
    module_db_session,
    module_sync_session,
    sync_session,
)
from .mocks import (
    mock_all_external_services,
    mock_celery,
    mock_external_apis,
    mock_httpx_client,
    mock_jwt_utils,
    mock_password_hasher,
    mock_redis,
    mock_s3_client,
    mock_web3,
)

__all__ = [
    # Base fixtures
    "async_engine",
    "test_app",
    # Database fixtures
    "db_session",
    "module_db_session",
    "sync_session",
    "module_sync_session",
    "clean_db_session",
    "clean_sync_session",
    # Authentication fixtures
    "test_user",
    "test_user_with_wallet",
    "admin_user",
    "inactive_user",
    "authenticated_client",
    "admin_authenticated_client",
    "create_user_and_wallet",
    "create_multiple_users",
    "create_user_with_tokens",
    # Client fixtures
    "client",
    "async_client",
    "client_with_db",
    "async_client_with_db",
    "client_authenticated",
    "authenticated_async_client",
    # Mock fixtures
    "mock_redis",
    "mock_web3",
    "mock_httpx_client",
    "mock_celery",
    "mock_s3_client",
    "mock_jwt_utils",
    "mock_password_hasher",
    "mock_external_apis",
    "mock_all_external_services",
    # Configuration fixtures
    "test_config",
    "mock_settings",
    "fixture_config",
    "test_data_config",
]
