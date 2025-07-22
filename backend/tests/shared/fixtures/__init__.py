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
- usecases.py: Usecase-specific fixtures with dependency injection
- repositories.py: Repository fixtures with dependency injection
- endpoints.py: API endpoint fixtures with dependency injection
- core.py: Core service fixtures (config, database, audit, etc.)
- services.py: Service-specific fixtures
- di_container.py: Dependency injection container fixtures

Usage:
    # Import specific fixtures
    from tests.fixtures.repositories import mock_user_repository, user_repository_with_di
    from tests.fixtures.usecases import mock_wallet_usecase, wallet_usecase_with_di
    from tests.fixtures.endpoints import users_endpoint_with_di, wallets_endpoint_with_di
    from tests.fixtures.core import mock_config, mock_database
    from tests.fixtures.auth import test_user, authenticated_client
    from tests.fixtures.client import client, async_client
    from tests.fixtures.mocks import mock_redis, mock_web3
    from tests.fixtures.test_data import sample_user, sample_wallet

    # Use in tests
    async def test_something(user_repository_with_di, mock_config, client):
        # Test implementation
        pass
"""

# Import all fixtures to make them available
from .auth import (
    admin_user,
    auth_usecase,
    authenticated_client,
    create_multiple_users,
    create_user_and_wallet,
    create_user_with_tokens,
    get_auth_headers_for_role_factory,
    get_auth_headers_for_user_factory,
    inactive_user,
    mock_refresh_token_repo,
    mock_user_repo,
    test_user,
    test_user_with_wallet,
)
from .base import async_engine, test_app
from .client import async_client, async_client_with_db, client, client_with_db
from .core import (
    mock_audit,
    mock_config,
    mock_database,
    mock_email_service,
    mock_jwt_utils,
    mock_session,
)
from .database import db_session
from .di_container import (
    integration_async_client,
    test_app_with_di_container,
    test_di_container_with_db,
)
from .endpoints import (
    admin_endpoint_with_di,
    auth_endpoint_with_di,
    email_verification_endpoint_with_di,
    health_endpoint_with_di,
    jwks_endpoint_with_di,
    oauth_endpoint_with_di,
    password_reset_endpoint_with_di,
    users_endpoint_with_di,
    wallets_endpoint_with_di,
)
from .jwks import sample_jwks
from .mocks import (
    mock_all_external_services,
    mock_async_session,
    mock_celery,
    mock_httpx_client,
    mock_password_hasher,
    mock_redis,
    mock_web3,
)
from .repositories import (
    email_verification_repository_with_di,
    historical_balance_repository_with_di,
    mock_email_verification_repository,
    mock_historical_balance_repository,
    mock_oauth_account_repository,
    mock_password_reset_repository,
    mock_portfolio_snapshot_repository,
    mock_refresh_token_repository,
    mock_token_balance_repository,
    mock_token_price_repository,
    mock_token_repository,
    mock_user_repository,
    mock_wallet_repository,
    oauth_account_repository_with_di,
    password_reset_repository_with_di,
    portfolio_snapshot_repository_with_di,
    refresh_token_repository_with_di,
    setup_mock_session,
    token_balance_repository_with_di,
    token_price_repository_with_di,
    token_repository_with_di,
    user_repository_with_di,
    wallet_repository_with_di,
)
from .services import mock_contract, oauth_service_with_di
from .usecases import (
    email_verification_usecase_with_di,
    historical_balance_usecase_with_di,
    mock_email_verification_usecase,
    oauth_usecase_with_di,
    portfolio_snapshot_usecase_with_di,
    token_balance_usecase_with_di,
    token_price_usecase_with_di,
    token_usecase_with_di,
    wallet_usecase_with_di,
)

__all__ = [
    # Base fixtures
    "async_engine",
    "test_app",
    # Database fixtures
    "db_session",
    # Authentication fixtures
    "test_user",
    "test_user_with_wallet",
    "admin_user",
    "inactive_user",
    "authenticated_client",
    "create_user_and_wallet",
    "create_multiple_users",
    "create_user_with_tokens",
    "get_auth_headers_for_user_factory",
    "get_auth_headers_for_role_factory",
    "mock_user_repo",
    "mock_refresh_token_repo",
    "auth_usecase",
    # Client fixtures
    "client",
    "async_client",
    "client_with_db",
    "async_client_with_db",
    # Mock fixtures
    "mock_redis",
    "mock_web3",
    "mock_async_session",
    "mock_httpx_client",
    "mock_celery",
    "mock_password_hasher",
    "mock_all_external_services",
    # Sample data fixtures
    "sample_jwks",
    # Service fixtures
    "mock_contract",
    "oauth_service_with_di",
    # Core Service fixtures
    "mock_config",
    "mock_database",
    "mock_audit",
    "mock_email_service",
    "mock_jwt_utils",
    "mock_session",
    # Repository fixtures
    "mock_user_repository",
    "mock_wallet_repository",
    "mock_email_verification_repository",
    "mock_oauth_account_repository",
    "mock_password_reset_repository",
    "mock_refresh_token_repository",
    "mock_portfolio_snapshot_repository",
    "mock_historical_balance_repository",
    "mock_token_repository",
    "mock_token_price_repository",
    "mock_token_balance_repository",
    "user_repository_with_di",
    "wallet_repository_with_di",
    "email_verification_repository_with_di",
    "oauth_account_repository_with_di",
    "password_reset_repository_with_di",
    "refresh_token_repository_with_di",
    "portfolio_snapshot_repository_with_di",
    "historical_balance_repository_with_di",
    "token_repository_with_di",
    "token_price_repository_with_di",
    "token_balance_repository_with_di",
    "setup_mock_session",
    "sample_jwks",
    # Usecase fixtures
    "mock_email_verification_usecase",
    "email_verification_usecase_with_di",
    "wallet_usecase_with_di",
    "oauth_usecase_with_di",
    "token_price_usecase_with_di",
    "token_usecase_with_di",
    "historical_balance_usecase_with_di",
    "token_balance_usecase_with_di",
    "portfolio_snapshot_usecase_with_di",
    # Endpoint fixtures
    "health_endpoint_with_di",
    "jwks_endpoint_with_di",
    "users_endpoint_with_di",
    "admin_endpoint_with_di",
    "email_verification_endpoint_with_di",
    "password_reset_endpoint_with_di",
    "oauth_endpoint_with_di",
    "auth_endpoint_with_di",
    "wallets_endpoint_with_di",
    "wallet_endpoint_with_di",
    # DI Container fixtures
    "test_di_container_with_db",
    "test_app_with_di_container",
    "integration_async_client",
]
