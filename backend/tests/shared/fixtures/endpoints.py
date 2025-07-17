"""
Endpoint fixtures for testing.

This module provides fixtures for testing API endpoints with dependency injection,
including endpoint instances with mocked dependencies.
"""

import pytest

# === ENDPOINT FIXTURES WITH DI ===


@pytest.fixture
def health_endpoint_with_di():
    """Create Health endpoint with mocked dependencies."""
    from app.api.endpoints.health import Health

    return Health()


@pytest.fixture
def jwks_endpoint_with_di():
    """Create JWKS endpoint with mocked dependencies."""
    from app.api.endpoints.jwks import JWKS

    return JWKS()


@pytest.fixture
def users_endpoint_with_di(mock_user_repository):
    """Create Users endpoint with mocked dependencies."""
    from app.api.endpoints.users import Users

    return Users(mock_user_repository)


@pytest.fixture
def admin_endpoint_with_di(mock_user_repository):
    """Create Admin endpoint with mocked dependencies."""
    from app.api.endpoints.admin import Admin

    return Admin(mock_user_repository)


@pytest.fixture
def email_verification_endpoint_with_di(mock_email_verification_usecase):
    """Create EmailVerification endpoint with mocked dependencies."""
    from app.api.endpoints.email_verification import EmailVerification

    return EmailVerification(mock_email_verification_usecase)


@pytest.fixture
def password_reset_endpoint_with_di(
    mock_password_reset_repository,
    mock_user_repository,
    mock_email_service,
):
    """Create PasswordReset endpoint with mocked dependencies."""
    from app.api.endpoints.password_reset import PasswordReset

    return PasswordReset(
        mock_password_reset_repository,
        mock_user_repository,
        mock_email_service,
    )


@pytest.fixture
def oauth_endpoint_with_di(oauth_usecase_with_di):
    """Create OAuth endpoint with mocked dependencies."""
    from app.api.endpoints.oauth import OAuth

    return OAuth(oauth_usecase_with_di)


@pytest.fixture
def auth_endpoint_with_di(mock_user_repository, mock_email_verification_repository):
    """Create Auth endpoint with mocked dependencies."""
    from app.api.endpoints.auth import Auth

    return Auth(mock_user_repository, mock_email_verification_repository)


@pytest.fixture
def wallets_endpoint_with_di(wallet_usecase_with_di):
    """Create Wallets endpoint with mocked dependencies."""
    from app.api.endpoints.wallets import Wallets

    return Wallets(wallet_usecase_with_di)


@pytest.fixture
def wallet_endpoint_with_di(wallet_usecase_with_di):
    """Create Wallet endpoint with mocked dependencies (alias for wallets_endpoint_with_di)."""
    from app.api.endpoints.wallets import Wallets

    return Wallets(wallet_usecase_with_di)
