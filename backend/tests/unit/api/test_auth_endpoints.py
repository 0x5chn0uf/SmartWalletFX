from __future__ import annotations

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.endpoints import auth
from app.api.endpoints.auth import Auth
from app.domain.errors import (
    InactiveUserError,
    InvalidCredentialsError,
    UnverifiedEmailError,
)
from app.domain.schemas.auth_token import TokenResponse
from app.domain.schemas.user import UserCreate, WeakPasswordError
from app.models.user import User
from app.services.auth_service import AuthService, DuplicateError


@pytest.fixture
def mock_auth_service():
    """Mock AuthService for testing."""
    mock_service = Mock(spec=AuthService)
    mock_service.register = AsyncMock()
    mock_service.authenticate = AsyncMock()
    mock_service.refresh_token = AsyncMock()
    mock_service.logout = AsyncMock()
    return mock_service


@pytest.fixture
def auth_endpoint(mock_auth_service):
    """Create Auth endpoint instance with mocked dependencies."""
    return Auth(mock_auth_service)


@pytest.mark.asyncio
async def test_register_user_success(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    background_tasks = Mock()

    user_payload = UserCreate(
        username="testuser", email="test@example.com", password="StrongP@ss123"
    )

    created_user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    mock_auth_service.register.return_value = created_user

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute
        result = await Auth.register_user(request, user_payload, background_tasks)

        # Assert
        assert result == created_user
        mock_auth_service.register.assert_awaited_once_with(
            user_payload, background_tasks=background_tasks
        )
        mock_audit.info.assert_called()


@pytest.mark.asyncio
async def test_register_user_duplicate_error(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    background_tasks = Mock()

    user_payload = UserCreate(
        username="testuser", email="test@example.com", password="StrongP@ss123"
    )

    mock_auth_service.register.side_effect = DuplicateError("username")

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await Auth.register_user(request, user_payload, background_tasks)

        assert excinfo.value.status_code == status.HTTP_409_CONFLICT
        assert excinfo.value.detail == "username already exists"
        mock_auth_service.register.assert_awaited_once_with(
            user_payload, background_tasks=background_tasks
        )
        mock_audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_weak_password(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    background_tasks = Mock()

    # Create a valid user payload by mocking the validator
    with patch("app.domain.schemas.user.validate_password_strength", return_value=True):
        user_payload = UserCreate(
            username="testuser", email="test@example.com", password="weak"
        )

    # Mock service methods
    mock_auth_service.register.side_effect = WeakPasswordError()

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await Auth.register_user(
            request=request,
            payload=user_payload,
            background_tasks=background_tasks,
        )

    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Password does not meet strength requirements" in excinfo.value.detail


@pytest.mark.asyncio
async def test_register_user_unexpected_error(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    background_tasks = Mock()

    user_payload = UserCreate(
        username="testuser", email="test@example.com", password="StrongP@ss123"
    )

    mock_auth_service.register.side_effect = Exception("Unexpected error")

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            await Auth.register_user(request, user_payload, background_tasks)

        assert str(excinfo.value) == "Unexpected error"
        mock_auth_service.register.assert_awaited_once_with(
            user_payload, background_tasks=background_tasks
        )
        mock_audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_login_for_access_token_success(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Mock(spec=Response)

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="StrongP@ss123", scope=""
    )

    tokens = TokenResponse(
        access_token="access_token",
        refresh_token="refresh_token",
        token_type="bearer",
        expires_in=3600,
    )

    mock_auth_service.authenticate.return_value = tokens

    mock_limiter = Mock()

    with patch(
        "app.api.endpoints.auth.deps_mod.login_rate_limiter", mock_limiter
    ), patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute
        result = await Auth.login_for_access_token(request, response, form_data)

        # Assert
        assert result == tokens
        mock_auth_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_limiter.reset.assert_called_once_with("127.0.0.1")
        mock_audit.info.assert_called()

        # Check that cookies were set
        response.set_cookie.assert_called()


@pytest.mark.asyncio
async def test_login_for_access_token_invalid_credentials(
    auth_endpoint, mock_auth_service
):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Mock(spec=Response)

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="wrongpassword", scope=""
    )

    mock_auth_service.authenticate.side_effect = InvalidCredentialsError()

    mock_limiter = Mock()
    mock_limiter.allow.return_value = True  # Not rate limited

    with patch(
        "app.api.endpoints.auth.deps_mod.login_rate_limiter", mock_limiter
    ), patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await Auth.login_for_access_token(request, response, form_data)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Invalid username or password"
        mock_auth_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_audit.warning.assert_called()


@pytest.mark.asyncio
async def test_login_for_access_token_rate_limited(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Mock(spec=Response)

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="wrongpassword", scope=""
    )

    mock_auth_service.authenticate.side_effect = InvalidCredentialsError()

    mock_limiter = Mock()
    mock_limiter.allow.return_value = False  # Rate limited

    with patch(
        "app.api.endpoints.auth.deps_mod.login_rate_limiter", mock_limiter
    ), patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await Auth.login_for_access_token(request, response, form_data)

        assert excinfo.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Too many login attempts" in excinfo.value.detail
        mock_auth_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_audit.warning.assert_called()


@pytest.mark.asyncio
async def test_login_for_access_token_inactive_user(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Mock(spec=Response)

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="StrongP@ss123", scope=""
    )

    mock_auth_service.authenticate.side_effect = InactiveUserError()

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await Auth.login_for_access_token(request, response, form_data)

        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == "Inactive or disabled user account"
        mock_auth_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_audit.warning.assert_called()


@pytest.mark.asyncio
async def test_login_for_access_token_unverified_email(
    auth_endpoint, mock_auth_service
):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Mock(spec=Response)

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="StrongP@ss123", scope=""
    )

    mock_auth_service.authenticate.side_effect = UnverifiedEmailError()

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await Auth.login_for_access_token(request, response, form_data)

        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == "Email address not verified"
        mock_auth_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_audit.warning.assert_called()


@pytest.mark.asyncio
async def test_login_for_access_token_unexpected_error(
    auth_endpoint, mock_auth_service
):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Mock(spec=Response)

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="StrongP@ss123", scope=""
    )

    mock_auth_service.authenticate.side_effect = Exception("Unexpected error")

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            await Auth.login_for_access_token(request, response, form_data)

        assert str(excinfo.value) == "Unexpected error"
        mock_auth_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_audit.error.assert_called()


@pytest.mark.asyncio
async def test_refresh_access_token_with_payload(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {}
    request.headers = {}  # Add headers attribute

    response = Mock(spec=Response)

    # Mock payload with refresh token
    payload = Mock()
    payload.refresh_token = "valid_refresh_token"

    tokens = TokenResponse(
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        token_type="bearer",
        expires_in=3600,
    )

    mock_auth_service.refresh_token.return_value = tokens

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute
        result = await Auth.refresh_access_token(request, response, payload)

        # Assert
        assert result == tokens
        mock_auth_service.refresh_token.assert_awaited_once_with("valid_refresh_token")
        mock_audit.info.assert_called()


@pytest.mark.asyncio
async def test_refresh_access_token_with_cookie(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {"refresh_token": "cookie_refresh_token"}
    request.headers = {}  # Add headers attribute

    response = Mock(spec=Response)

    # No payload
    payload = None

    tokens = TokenResponse(
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        token_type="bearer",
        expires_in=3600,
    )

    mock_auth_service.refresh_token.return_value = tokens

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute
        result = await Auth.refresh_access_token(request, response, payload)

        # Assert
        assert result == tokens
        mock_auth_service.refresh_token.assert_awaited_once_with("cookie_refresh_token")
        mock_audit.info.assert_called()


@pytest.mark.asyncio
async def test_refresh_access_token_no_token(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {}
    request.headers = {}  # Add headers attribute

    response = Mock(spec=Response)

    # No payload and no cookie
    payload = None

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await Auth.refresh_access_token(request, response, payload)

        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Refresh token not provided" in excinfo.value.detail
        mock_audit.warning.assert_called()


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_token(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {}
    request.headers = {}  # Add headers attribute

    response = Mock(spec=Response)

    # Mock payload with invalid refresh token
    payload = Mock()
    payload.refresh_token = "invalid_refresh_token"

    mock_auth_service.refresh_token.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await Auth.refresh_access_token(request, response, payload)

        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert excinfo.value.detail == "Invalid refresh token"
        mock_auth_service.refresh_token.assert_awaited_once_with(
            "invalid_refresh_token"
        )


@pytest.mark.asyncio
async def test_logout_success(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {"refresh_token": "valid_refresh_token"}

    response = Mock(spec=Response)

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute
        result = await Auth.logout(request, response)

        # Assert
        assert result is None
        # Verify cookies are cleared
        response.delete_cookie.assert_any_call("access_token")
        response.delete_cookie.assert_any_call("refresh_token", path="/auth/refresh")
        # Verify audit logging
        mock_audit.info.assert_any_call("User logout started", client_ip="127.0.0.1")
        mock_audit.info.assert_any_call("User logout completed", client_ip="127.0.0.1")
        mock_audit.info.assert_called()

        # Check that cookies were deleted
        response.delete_cookie.assert_called()


@pytest.mark.asyncio
async def test_logout_no_token(auth_endpoint, mock_auth_service):
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {}

    response = Mock(spec=Response)

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await Auth.logout(request, response)

        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Refresh token not provided" in excinfo.value.detail
        mock_auth_service.logout.assert_not_awaited()
        mock_audit.warning.assert_called()
