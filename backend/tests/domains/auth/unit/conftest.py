"""Shared fixtures for auth service and endpoint tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from app.api.endpoints.auth import Auth
from app.core.config import Configuration
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.usecase.auth_usecase import AuthUsecase
from app.utils.jwt import JWTUtils
from app.utils.logging import Audit
from app.utils.rate_limiter import RateLimiterUtils


@pytest.fixture
def mock_user_repo():
    """Mock UserRepository."""
    mock = AsyncMock(spec=UserRepository)

    # Track saved users to simulate duplicate checking for registration tests
    saved_users = []

    async def get_by_username_side_effect(username):
        return next((user for user in saved_users if user.username == username), None)

    async def get_by_email_side_effect(email):
        return next((user for user in saved_users if user.email == email), None)

    async def save_side_effect(user):
        saved_users.append(user)
        # Check if a specific return_value was set, use that instead
        if hasattr(mock.save, "return_value") and mock.save.return_value is not None:
            return mock.save.return_value
        return user

    # Don't set side effects by default - let tests override as needed
    mock.save.side_effect = save_side_effect

    # Store references to side effects so registration tests can enable them
    mock._username_side_effect = get_by_username_side_effect
    mock._email_side_effect = get_by_email_side_effect

    return mock


@pytest.fixture
def mock_email_verification_repo():
    """Mock EmailVerificationRepository."""
    return AsyncMock(spec=EmailVerificationRepository)


@pytest.fixture
def mock_refresh_token_repo():
    """Mock RefreshTokenRepository."""
    return AsyncMock(spec=RefreshTokenRepository)


@pytest.fixture
def mock_email_service():
    """Mock EmailService."""
    return Mock(spec=EmailService)


@pytest.fixture
def mock_jwt_utils():
    """Mock JWTUtils."""
    mock = Mock(spec=JWTUtils)
    mock.decode_token = Mock()
    mock.create_access_token = Mock()
    # Return a valid, decodable JWT for the refresh token
    mock.create_refresh_token.return_value = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJqdGkiOiJ0ZXN0LWp0aSJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    return mock


@pytest.fixture
def mock_config():
    """Mock Configuration."""
    mock = Mock(spec=Configuration)
    mock.ACTIVE_JWT_KID = "test-kid"
    mock.EMAIL_VERIFICATION_EXPIRE_MINUTES = 1440
    mock.FRONTEND_BASE_URL = "http://test-frontend.com"
    mock.REFRESH_TOKEN_EXPIRE_DAYS = 7
    mock.ACCESS_TOKEN_EXPIRE_MINUTES = 15
    return mock


@pytest.fixture
def mock_audit():
    """Mock Audit service."""
    return Mock(spec=Audit)


@pytest.fixture
def auth_usecase(
    mock_user_repo,
    mock_email_verification_repo,
    mock_refresh_token_repo,
    mock_email_service,
    mock_jwt_utils,
    mock_config,
    mock_audit,
):
    """Provides an AuthUsecase instance with mocked dependencies."""
    from app.usecase.auth_usecase import AuthUsecase

    return AuthUsecase(
        user_repository=mock_user_repo,
        email_verification_repository=mock_email_verification_repo,
        refresh_token_repository=mock_refresh_token_repo,
        email_service=mock_email_service,
        jwt_utils=mock_jwt_utils,
        config=mock_config,
        audit=mock_audit,
    )


@pytest.fixture
def mock_auth_usecase():
    """Mock AuthUsecase for testing endpoints."""
    mock_usecase = Mock(spec=AuthUsecase)
    mock_usecase.register = AsyncMock()
    mock_usecase.authenticate = AsyncMock()
    mock_usecase.refresh = AsyncMock()
    mock_usecase.logout = AsyncMock()
    return mock_usecase


@pytest.fixture
def mock_rate_limiter_utils():
    """Mock RateLimiterUtils."""
    mock = Mock(spec=RateLimiterUtils)
    mock.login_rate_limiter = Mock()
    mock.login_rate_limiter.allow = Mock(return_value=True)
    mock.login_rate_limiter.reset = Mock()
    mock.login_rate_limiter.clear = Mock()
    return mock


@pytest.fixture
def auth_endpoint(mock_auth_usecase, mock_rate_limiter_utils):
    """Create Auth endpoint instance with mocked dependencies."""
    return Auth(mock_auth_usecase, mock_rate_limiter_utils)
