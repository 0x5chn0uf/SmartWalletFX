"""Test auth token endpoints."""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request, Response, status

from app.api.endpoints.auth import Auth
from app.domain.schemas.auth_token import TokenResponse


class TestAuthTokenEndpoints:
    """Test auth token endpoints."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_refresh_access_token_with_payload(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test token refresh with payload."""
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

        mock_auth_usecase.refresh.return_value = tokens

        with patch("app.api.endpoints.auth.Audit") as mock_audit, patch.object(
            Auth, "_auth_usecase", mock_auth_usecase
        ):
            # Execute
            result = await Auth.refresh_access_token(request, response, payload)

            # Assert
            assert result == tokens
            mock_auth_usecase.refresh.assert_awaited_once_with("valid_refresh_token")
            mock_audit.info.assert_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_refresh_access_token_with_cookie(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test token refresh with cookie."""
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

        mock_auth_usecase.refresh.return_value = tokens

        with patch("app.api.endpoints.auth.Audit") as mock_audit, patch.object(
            Auth, "_auth_usecase", mock_auth_usecase
        ):
            # Execute
            result = await Auth.refresh_access_token(request, response, payload)

            # Assert
            assert result == tokens
            mock_auth_usecase.refresh.assert_awaited_once_with("cookie_refresh_token")
            mock_audit.info.assert_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_refresh_access_token_no_token(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test token refresh with no token."""
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

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid_token(
        self, auth_endpoint, mock_auth_usecase
    ):
        """Test token refresh with invalid token."""
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

        mock_auth_usecase.refresh.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

        with patch("app.api.endpoints.auth.Audit"), patch.object(
            Auth, "_auth_usecase", mock_auth_usecase
        ):
            # Execute and Assert
            with pytest.raises(HTTPException) as excinfo:
                await Auth.refresh_access_token(request, response, payload)

            assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert excinfo.value.detail == "Invalid refresh token"
            mock_auth_usecase.refresh.assert_awaited_once_with("invalid_refresh_token")
