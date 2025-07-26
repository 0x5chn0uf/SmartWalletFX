"""Test auth logout endpoints."""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request, Response, status

from app.api.endpoints.auth import Auth


class TestAuthLogoutEndpoints:
    """Test auth logout endpoints."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_logout_success(self, auth_endpoint, mock_auth_usecase):
        """Test successful logout."""
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
            response.delete_cookie.assert_any_call("refresh_token", path="/auth")
            # Verify audit logging
            mock_audit.info.assert_any_call(
                "User logout started", client_ip="127.0.0.1"
            )
            mock_audit.info.assert_any_call(
                "User logout completed", client_ip="127.0.0.1"
            )
            mock_audit.info.assert_called()

            # Check that cookies were deleted
            response.delete_cookie.assert_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_logout_no_token(self, auth_endpoint, mock_auth_usecase):
        """Test logout with no token."""
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
            mock_auth_usecase.logout.assert_not_awaited()
            mock_audit.warning.assert_called()
