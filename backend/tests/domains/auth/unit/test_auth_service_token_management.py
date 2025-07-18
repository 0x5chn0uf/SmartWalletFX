"""Test auth service token management functionality."""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest


class TestAuthServiceTokenManagement:
    """Test auth service token management functionality."""

    @pytest.mark.asyncio
    async def test_revoke_refresh_token_success(
        self, auth_usecase, mock_refresh_token_repo, mock_jwt_utils
    ):
        """Test successful token revocation."""
        # Setup
        mock_jwt_utils.decode_token.return_value = {"jti": "test-jti"}
        mock_token = Mock()
        mock_token.revoked = False
        mock_refresh_token_repo.get_by_jti_hash.return_value = mock_token

        # Execute
        with patch("app.usecase.auth_usecase.sha256") as mock_sha256:
            mock_sha256.return_value.hexdigest.return_value = "hashed-jti"
            await auth_usecase.revoke_refresh_token(
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJqdGkiOiJ0ZXN0LWp0aSJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            )

            # Verify
            mock_refresh_token_repo.get_by_jti_hash.assert_called_once_with(
                "hashed-jti"
            )
            mock_refresh_token_repo.save.assert_called_once()
            saved_token = mock_refresh_token_repo.save.call_args[0][0]
            assert saved_token.revoked is True

    @pytest.mark.asyncio
    async def test_revoke_refresh_token_not_found(
        self, auth_usecase, mock_refresh_token_repo, mock_jwt_utils
    ):
        """Test token revocation when token not found."""
        mock_jwt_utils.decode_token.return_value = {"jti": "not-found-jti"}
        mock_refresh_token_repo.get_by_jti_hash.return_value = None

        # Execute and Verify (should not raise error)
        await auth_usecase.revoke_refresh_token("some-token")
        mock_refresh_token_repo.save.assert_not_called()
