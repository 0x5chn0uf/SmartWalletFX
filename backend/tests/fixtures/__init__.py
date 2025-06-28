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
- test_data.py: Sample data and model fixtures
- usecase.py: Usecase-specific fixtures
- services.py: Service-specific fixtures

Usage:
    # Import specific fixtures
    from tests.fixtures.database import db_session, sync_session
    from tests.fixtures.auth import test_user, authenticated_client
    from tests.fixtures.client import client, async_client
    from tests.fixtures.mocks import mock_redis, mock_web3
    from tests.fixtures.test_data import sample_user, sample_wallet
    from tests.fixtures.usecase import historical_balance_usecase, sample_historical_balance_data
    from tests.fixtures.services import portfolio_service, mock_snapshot_data

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
    mock_async_session,
    mock_celery,
    mock_db_session,
    mock_external_apis,
    mock_httpx_client,
    mock_jwt_utils,
    mock_password_hasher,
    mock_redis,
    mock_s3_client,
    mock_web3,
)
from .services import (
    blockchain_service,
    mock_contract,
    mock_snapshot_data,
    mock_web3_for_blockchain,
    portfolio_service,
)
from .test_data import (
    sample_aggregate_metrics,
    sample_historical_balance,
    sample_historical_data,
    sample_portfolio_data,
    sample_portfolio_snapshot,
    sample_user,
    sample_wallet,
    sample_wallet_data,
)
from .usecase import historical_balance_usecase, sample_historical_balance_data

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
    "mock_web3_for_blockchain",
    "mock_async_session",
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
    # Sample data fixtures
    "sample_user",
    "sample_wallet",
    "sample_portfolio_snapshot",
    "sample_historical_balance",
    "sample_aggregate_metrics",
    "sample_wallet_data",
    "sample_historical_data",
    "sample_portfolio_data",
    # Usecase fixtures
    "historical_balance_usecase",
    "mock_db_session",
    "sample_historical_balance_data",
    # Service fixtures
    "portfolio_service",
    "blockchain_service",
    "mock_contract",
    "mock_snapshot_data",
]
