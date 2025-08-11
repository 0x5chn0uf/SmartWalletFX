"""Test auth service token refresh functionality."""
from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.domain.errors import InvalidCredentialsError


class TestAuthServiceTokenRefresh:
    """Test auth service token refresh functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_refresh_success(
        self, auth_usecase, mock_jwt_utils, mock_refresh_token_repo
    ):
        """Test successful token refresh."""
        # Setup mock JWT utils
        mock_jwt_utils.decode_token.return_value = {
            "sub": "1",
            "type": "refresh",
            "jti": "test-jti",
        }
        mock_jwt_utils.create_access_token.return_value = "new-access-token"

        # Setup mock refresh token repository
        mock_token = Mock()
        mock_token.revoked = False
        mock_refresh_token_repo.get_by_jti_hash.return_value = mock_token

        # Execute
        result = await auth_usecase.refresh("valid-refresh-token")

        # Verify
        assert result.access_token == "new-access-token"
        assert result.token_type == "bearer"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, auth_usecase, mock_jwt_utils):
        """Test refresh with invalid token."""
        mock_jwt_utils.decode_token.side_effect = Exception("Invalid token")

        with pytest.raises(InvalidCredentialsError):
            await auth_usecase.refresh("invalid-token")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_refresh_wrong_token_type(self, auth_usecase, mock_jwt_utils):
        """Test refresh with wrong token type."""
        mock_jwt_utils.decode_token.return_value = {
            "sub": "1",
            "type": "access",  # Wrong type
            "jti": "test-jti",
        }

        with pytest.raises(InvalidCredentialsError):
            await auth_usecase.refresh("wrong-type-token")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_refresh_expired_token(
        self, auth_usecase, mock_jwt_utils, mock_refresh_token_repo
    ):
        """Test refresh with expired token."""
        mock_jwt_utils.decode_token.return_value = {
            "sub": "1",
            "type": "refresh",
            "jti": "test-jti",
        }
        mock_refresh_token_repo.get_by_jti_hash.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await auth_usecase.refresh("expired-token")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_refresh_revoked_token(
        self, auth_usecase, mock_jwt_utils, mock_refresh_token_repo
    ):
        """Test refresh with revoked token."""
        mock_jwt_utils.decode_token.return_value = {
            "sub": "1",
            "type": "refresh",
            "jti": "test-jti",
        }

        mock_token = Mock()
        mock_token.revoked = True
        mock_refresh_token_repo.get_by_jti_hash.return_value = mock_token

        with pytest.raises(InvalidCredentialsError):
            await auth_usecase.refresh("revoked-token")
