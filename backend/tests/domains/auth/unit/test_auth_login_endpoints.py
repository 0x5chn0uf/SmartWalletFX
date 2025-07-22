"""Test auth login endpoints."""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.endpoints.auth import Auth
from app.domain.errors import (
    InactiveUserError,
    InvalidCredentialsError,
    UnverifiedEmailError,
)
from app.domain.schemas.auth_token import TokenResponse


class TestAuthLoginEndpoints:
    """Test auth login endpoints."""

    @pytest.mark.asyncio
    async def test_login_for_access_token_success(
        self, auth_endpoint, mock_auth_usecase, mock_rate_limiter_utils
    ):
        """Test successful login."""
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

        mock_auth_usecase.authenticate.return_value = tokens

        with patch("app.api.endpoints.auth.Audit") as mock_audit:
            # Execute
            result = await auth_endpoint.login_for_access_token(
                request, response, form_data
            )

            # Assert
            assert result == tokens
            mock_auth_usecase.authenticate.assert_awaited_once_with(
                form_data.username, form_data.password
            )
            mock_rate_limiter_utils.login_rate_limiter.reset.assert_called_once_with(
                "127.0.0.1"
            )
            mock_audit.info.assert_called()

            # Check that cookies were set
            response.set_cookie.assert_called()

    @pytest.mark.asyncio
    async def test_login_for_access_token_invalid_credentials(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test login with invalid credentials."""
        # Setup
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"

        response = Mock(spec=Response)

        form_data = OAuth2PasswordRequestForm(
            username="testuser", password="wrongpassword", scope=""
        )

        mock_auth_usecase.authenticate.side_effect = InvalidCredentialsError()

        mock_limiter = Mock()
        mock_limiter.allow.return_value = True  # Not rate limited

        # Mock the rate limiter on the Auth class
        Auth._rate_limiter_utils.login_rate_limiter = mock_limiter

        with patch("app.api.endpoints.auth.Audit") as mock_audit:
            # Execute and Assert
            with pytest.raises(HTTPException) as excinfo:
                await Auth.login_for_access_token(request, response, form_data)

            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Invalid username or password"
            mock_auth_usecase.authenticate.assert_awaited_once_with(
                form_data.username, form_data.password
            )
            mock_audit.warning.assert_called()

    @pytest.mark.asyncio
    async def test_login_for_access_token_rate_limited(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test login when rate limited."""
        # Setup
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"

        response = Mock(spec=Response)

        form_data = OAuth2PasswordRequestForm(
            username="testuser", password="wrongpassword", scope=""
        )

        mock_auth_usecase.authenticate.side_effect = InvalidCredentialsError()

        mock_limiter = Mock()
        mock_limiter.allow.return_value = False  # Rate limited

        with patch.object(Auth, "_rate_limiter_utils") as mock_rate_limiter_utils:
            mock_rate_limiter_utils.login_rate_limiter = mock_limiter
            with patch("app.api.endpoints.auth.Audit") as mock_audit:
                # Execute and Assert
                with pytest.raises(HTTPException) as excinfo:
                    await Auth.login_for_access_token(request, response, form_data)

                assert excinfo.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                assert "Too many login attempts" in excinfo.value.detail
                mock_auth_usecase.authenticate.assert_awaited_once_with(
                    form_data.username, form_data.password
                )
                mock_audit.warning.assert_called()

    @pytest.mark.asyncio
    async def test_login_for_access_token_inactive_user(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test login with inactive user."""
        # Setup
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"

        response = Mock(spec=Response)

        form_data = OAuth2PasswordRequestForm(
            username="testuser", password="StrongP@ss123", scope=""
        )

        mock_auth_usecase.authenticate.side_effect = InactiveUserError()

        with patch("app.api.endpoints.auth.Audit") as mock_audit:
            # Execute and Assert
            with pytest.raises(HTTPException) as excinfo:
                await Auth.login_for_access_token(request, response, form_data)

            assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
            assert excinfo.value.detail == "Inactive or disabled user account"
            mock_auth_usecase.authenticate.assert_awaited_once_with(
                form_data.username, form_data.password
            )
            mock_audit.warning.assert_called()

    @pytest.mark.asyncio
    async def test_login_for_access_token_unverified_email(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test login with unverified email."""
        # Setup
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"

        response = Mock(spec=Response)

        form_data = OAuth2PasswordRequestForm(
            username="testuser", password="StrongP@ss123", scope=""
        )

        mock_auth_usecase.authenticate.side_effect = UnverifiedEmailError()

        with patch("app.api.endpoints.auth.Audit") as mock_audit:
            # Execute and Assert
            with pytest.raises(HTTPException) as excinfo:
                await Auth.login_for_access_token(request, response, form_data)

            assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
            assert excinfo.value.detail == "Email address not verified"
            mock_auth_usecase.authenticate.assert_awaited_once_with(
                form_data.username, form_data.password
            )
            mock_audit.warning.assert_called()

    @pytest.mark.asyncio
    async def test_login_for_access_token_unexpected_error(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test login with unexpected error."""
        # Setup
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"

        response = Mock(spec=Response)

        form_data = OAuth2PasswordRequestForm(
            username="testuser", password="StrongP@ss123", scope=""
        )

        mock_auth_usecase.authenticate.side_effect = Exception("Unexpected error")

        with patch("app.api.endpoints.auth.Audit") as mock_audit:
            # Execute and Assert
            with pytest.raises(Exception) as excinfo:
                await Auth.login_for_access_token(request, response, form_data)

            assert str(excinfo.value) == "Unexpected error"
            mock_auth_usecase.authenticate.assert_awaited_once_with(
                form_data.username, form_data.password
            )
            mock_audit.error.assert_called()
