from __future__ import annotations

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.endpoints import auth
from app.domain.errors import (
    InactiveUserError,
    InvalidCredentialsError,
    UnverifiedEmailError,
)
from app.models.user import User
from app.schemas.auth_token import TokenResponse
from app.schemas.user import UserCreate, WeakPasswordError
from app.services.auth_service import AuthService, DuplicateError


@pytest.mark.asyncio
async def test_register_user_success():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    background_tasks = Mock()
    db = AsyncMock(spec=AsyncSession)

    user_payload = UserCreate(
        username="testuser", email="test@example.com", password="StrongP@ss123"
    )

    created_user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    mock_service = AsyncMock(spec=AuthService)
    mock_service.register.return_value = created_user

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.Audit"
    ) as mock_audit:
        # Execute
        result = await auth.register_user(request, user_payload, background_tasks, db)

        # Assert
        assert result == created_user
        mock_service.register.assert_awaited_once_with(
            user_payload, background_tasks=background_tasks
        )
        mock_audit.info.assert_called()


@pytest.mark.asyncio
async def test_register_user_duplicate_error():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    background_tasks = Mock()
    db = AsyncMock(spec=AsyncSession)

    user_payload = UserCreate(
        username="testuser", email="test@example.com", password="StrongP@ss123"
    )

    mock_service = AsyncMock(spec=AuthService)
    mock_service.register.side_effect = DuplicateError("username")

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.Audit"
    ) as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await auth.register_user(request, user_payload, background_tasks, db)

        assert excinfo.value.status_code == status.HTTP_409_CONFLICT
        assert excinfo.value.detail == "username already exists"
        mock_service.register.assert_awaited_once_with(
            user_payload, background_tasks=background_tasks
        )
        mock_audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_weak_password():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    background_tasks = Mock()
    db = AsyncMock(spec=AsyncSession)

    # Create a valid user payload by mocking the validator
    with patch("app.schemas.user.validate_password_strength", return_value=True):
        user_payload = UserCreate(
            username="testuser", email="test@example.com", password="weak"
        )

    # Mock service methods
    auth_service = AsyncMock(spec=AuthService)
    auth_service.register.side_effect = WeakPasswordError()

    # Execute and Assert
    with patch("app.api.endpoints.auth.AuthService", return_value=auth_service):
        with pytest.raises(HTTPException) as excinfo:
            await auth.register_user(
                request=request,
                payload=user_payload,
                background_tasks=background_tasks,
                db=db,
            )

        assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Password does not meet strength requirements" in excinfo.value.detail


@pytest.mark.asyncio
async def test_register_user_unexpected_error():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    background_tasks = Mock()
    db = AsyncMock(spec=AsyncSession)

    user_payload = UserCreate(
        username="testuser", email="test@example.com", password="StrongP@ss123"
    )

    mock_service = AsyncMock(spec=AuthService)
    mock_service.register.side_effect = Exception("Unexpected error")

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.Audit"
    ) as mock_audit:
        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            await auth.register_user(request, user_payload, background_tasks, db)

        assert str(excinfo.value) == "Unexpected error"
        mock_service.register.assert_awaited_once_with(
            user_payload, background_tasks=background_tasks
        )
        mock_audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_login_for_access_token_success():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Mock(spec=Response)

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="StrongP@ss123", scope=""
    )

    db = AsyncMock(spec=AsyncSession)

    tokens = TokenResponse(
        access_token="access_token",
        refresh_token="refresh_token",
        token_type="bearer",
        expires_in=3600,
    )

    mock_service = AsyncMock(spec=AuthService)
    mock_service.authenticate.return_value = tokens

    mock_limiter = Mock()

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.deps_mod.login_rate_limiter", mock_limiter
    ), patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute
        result = await auth.login_for_access_token(request, response, form_data, db)

        # Assert
        assert result == tokens
        mock_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_limiter.reset.assert_called_once_with("127.0.0.1")
        mock_audit.info.assert_called()

        # Check that cookies were set
        response.set_cookie.assert_any_call(
            "access_token",
            tokens.access_token,
            httponly=True,
            samesite="lax",
        )
        response.set_cookie.assert_any_call(
            "refresh_token",
            tokens.refresh_token,
            httponly=True,
            samesite="lax",
            path="/auth/refresh",
        )


@pytest.mark.asyncio
async def test_login_for_access_token_invalid_credentials():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Response()

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="WrongPassword", scope=""
    )

    db = AsyncMock(spec=AsyncSession)

    mock_service = AsyncMock(spec=AuthService)
    mock_service.authenticate.side_effect = InvalidCredentialsError(
        "Invalid credentials"
    )

    mock_limiter = Mock()
    mock_limiter.allow.return_value = True

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.deps_mod.login_rate_limiter", mock_limiter
    ), patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await auth.login_for_access_token(request, response, form_data, db)

        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert excinfo.value.detail == "Invalid username or password"
        mock_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_limiter.allow.assert_called_once_with("127.0.0.1")
        mock_audit.warning.assert_called_once()


@pytest.mark.asyncio
async def test_login_for_access_token_rate_limited():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Response()

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="WrongPassword", scope=""
    )

    db = AsyncMock(spec=AsyncSession)

    mock_service = AsyncMock(spec=AuthService)
    mock_service.authenticate.side_effect = InvalidCredentialsError(
        "Invalid credentials"
    )

    mock_limiter = Mock()
    mock_limiter.allow.return_value = False

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.deps_mod.login_rate_limiter", mock_limiter
    ), patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await auth.login_for_access_token(request, response, form_data, db)

        assert excinfo.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert (
            excinfo.value.detail == "Too many login attempts, please try again later."
        )
        mock_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_limiter.allow.assert_called_once_with("127.0.0.1")
        mock_audit.warning.assert_called()


@pytest.mark.asyncio
async def test_login_for_access_token_inactive_user():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Response()

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="StrongP@ss123", scope=""
    )

    db = AsyncMock(spec=AsyncSession)

    mock_service = AsyncMock(spec=AuthService)
    mock_service.authenticate.side_effect = InactiveUserError("Inactive user")

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.deps_mod.login_rate_limiter", Mock()
    ), patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await auth.login_for_access_token(request, response, form_data, db)

        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == "Inactive or disabled user account"
        mock_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_audit.warning.assert_called_once()


@pytest.mark.asyncio
async def test_login_for_access_token_unverified_email():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Response()

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="StrongP@ss123", scope=""
    )

    db = AsyncMock(spec=AsyncSession)

    mock_service = AsyncMock(spec=AuthService)
    mock_service.authenticate.side_effect = UnverifiedEmailError("Email not verified")

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.deps_mod.login_rate_limiter", Mock()
    ), patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await auth.login_for_access_token(request, response, form_data, db)

        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == "Email address not verified"
        mock_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_audit.warning.assert_called_once()


@pytest.mark.asyncio
async def test_login_for_access_token_unexpected_error():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Response()

    form_data = OAuth2PasswordRequestForm(
        username="testuser", password="StrongP@ss123", scope=""
    )

    db = AsyncMock(spec=AsyncSession)

    mock_service = AsyncMock(spec=AuthService)
    mock_service.authenticate.side_effect = Exception("Unexpected error")

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.deps_mod.login_rate_limiter", Mock()
    ), patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute and Assert
        with pytest.raises(Exception) as excinfo:
            await auth.login_for_access_token(request, response, form_data, db)

        assert str(excinfo.value) == "Unexpected error"
        mock_service.authenticate.assert_awaited_once_with(
            form_data.username, form_data.password
        )
        mock_audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_access_token_with_payload():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Mock(spec=Response)

    payload = auth._RefreshRequest(refresh_token="refresh_token")

    db = AsyncMock(spec=AsyncSession)

    tokens = TokenResponse(
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        token_type="bearer",
        expires_in=3600,
    )

    mock_service = AsyncMock(spec=AuthService)
    mock_service.refresh.return_value = tokens

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.Audit"
    ) as mock_audit:
        # Execute
        result = await auth.refresh_access_token(request, response, payload, db)

        # Assert
        assert result == tokens
        mock_service.refresh.assert_awaited_once_with("refresh_token")
        mock_audit.info.assert_called()

        # Check that cookies were set
        response.set_cookie.assert_any_call(
            "access_token",
            tokens.access_token,
            httponly=True,
            samesite="lax",
        )


@pytest.mark.asyncio
async def test_refresh_access_token_with_cookie():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {"refresh_token": "cookie_refresh_token"}

    response = Mock(spec=Response)

    payload = None

    db = AsyncMock(spec=AsyncSession)

    tokens = TokenResponse(
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        token_type="bearer",
        expires_in=3600,
    )

    mock_service = AsyncMock(spec=AuthService)
    mock_service.refresh.return_value = tokens

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.Audit"
    ) as mock_audit, patch("app.api.endpoints.auth.time.time", return_value=123456789):
        # Execute
        result = await auth.refresh_access_token(request, response, payload, db)

        # Assert
        assert result == tokens
        mock_service.refresh.assert_awaited_once_with("cookie_refresh_token")
        mock_audit.info.assert_called()

        # Check that cookies were set
        response.set_cookie.assert_any_call(
            "access_token",
            tokens.access_token,
            httponly=True,
            samesite="lax",
        )


@pytest.mark.asyncio
async def test_refresh_access_token_no_token():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {}

    response = Mock(spec=Response)

    payload = None

    db = AsyncMock(spec=AsyncSession)

    with patch("app.api.endpoints.auth.Audit") as mock_audit:
        # Execute
        result = await auth.refresh_access_token(request, response, payload, db)

        # Assert
        assert result.status_code == status.HTTP_204_NO_CONTENT
        mock_audit.info.assert_called()


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_token():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    response = Mock(spec=Response)

    payload = auth._RefreshRequest(refresh_token="invalid_token")

    db = AsyncMock(spec=AsyncSession)

    mock_service = AsyncMock(spec=AuthService)
    mock_service.refresh.side_effect = Exception("Invalid token")

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.Audit"
    ) as mock_audit:
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await auth.refresh_access_token(request, response, payload, db)

        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert excinfo.value.detail == "Invalid or expired refresh token"
        mock_service.refresh.assert_awaited_once_with("invalid_token")
        mock_audit.warning.assert_called_once()


@pytest.mark.asyncio
async def test_logout_success():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {"refresh_token": "refresh_token"}

    response = Mock(spec=Response)

    db = AsyncMock(spec=AsyncSession)

    mock_service = AsyncMock(spec=AuthService)

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.Audit"
    ) as mock_audit:
        # Execute
        result = await auth.logout(request, response, db)

        # Assert
        assert result is None
        mock_service.revoke_refresh_token.assert_awaited_once_with("refresh_token")
        mock_audit.info.assert_called_once()

        # Check that cookies were cleared
        response.set_cookie.assert_any_call(
            "access_token",
            "",
            max_age=0,
            path="/",
            httponly=True,
            secure=False,
            samesite="lax",
        )
        response.set_cookie.assert_any_call(
            "refresh_token",
            "",
            max_age=0,
            path="/auth/refresh",
            httponly=True,
            secure=False,
            samesite="lax",
        )


@pytest.mark.asyncio
async def test_logout_no_token():
    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.cookies = {}

    response = Mock(spec=Response)

    db = AsyncMock(spec=AsyncSession)

    mock_service = AsyncMock(spec=AuthService)

    with patch("app.api.endpoints.auth.AuthService", return_value=mock_service), patch(
        "app.api.endpoints.auth.Audit"
    ) as mock_audit:
        # Execute
        result = await auth.logout(request, response, db)

        # Assert
        assert result is None
        mock_service.revoke_refresh_token.assert_not_awaited()
        mock_audit.info.assert_called_once()

        # Check that cookies were cleared
        response.set_cookie.assert_any_call(
            "access_token",
            "",
            max_age=0,
            path="/",
            httponly=True,
            secure=False,
            samesite="lax",
        )
        response.set_cookie.assert_any_call(
            "refresh_token",
            "",
            max_age=0,
            path="/auth/refresh",
            httponly=True,
            secure=False,
            samesite="lax",
        )
