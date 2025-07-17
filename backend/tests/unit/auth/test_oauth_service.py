from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models.user import User


class TestOAuthService:
    """Test OAuthService using new dependency injection pattern."""

    @pytest.mark.asyncio
    async def test_authenticate_creates_user_if_missing(
        self,
        oauth_service_with_di,
        mock_user_repository,
        mock_oauth_account_repository,
        mock_audit,
    ):
        """Test that authenticate_or_create creates a new user if none exists."""
        # Setup mocks - no existing OAuth account or user (make them async)
        mock_oauth_account_repository.get_by_provider_account = AsyncMock(
            return_value=None
        )
        mock_oauth_account_repository.link_account = AsyncMock()
        mock_user_repository.get_by_email = AsyncMock(return_value=None)

        created_user = User(
            id=uuid.uuid4(), username="alice", email="alice@example.com"
        )
        mock_user_repository.save = AsyncMock(return_value=created_user)

        # Execute
        user = await oauth_service_with_di.authenticate_or_create(
            "google", "account123", "alice@example.com"
        )

        # Verify
        assert user == created_user
        mock_oauth_account_repository.get_by_provider_account.assert_awaited_once_with(
            "google", "account123"
        )
        mock_user_repository.get_by_email.assert_awaited_once_with("alice@example.com")
        mock_user_repository.save.assert_awaited()
        mock_audit.info.assert_called()

    @pytest.mark.asyncio
    async def test_issue_tokens(
        self,
        oauth_service_with_di,
        mock_refresh_token_repository,
        mock_jwt_utils,
        mock_audit,
    ):
        """Test that issue_tokens creates access and refresh tokens."""
        user = User(id=uuid.uuid4(), username="test", email="test@example.com")

        # Mock JWT utils to return test tokens
        mock_jwt_utils.create_access_token.return_value = "test_access_token"
        mock_jwt_utils.create_refresh_token.return_value = "test_refresh_token"

        # Mock the JWT claims extraction to avoid JWT decoding issues
        with patch(
            "app.services.oauth_service.jose_jwt.get_unverified_claims"
        ) as mock_get_claims:
            mock_get_claims.return_value = {"jti": "test_jti"}
            mock_refresh_token_repository.create_from_jti = AsyncMock()

            # Mock the config service to return a proper integer for TTL
            oauth_service_with_di._OAuthService__config_service.REFRESH_TOKEN_EXPIRE_DAYS = (
                7
            )
            oauth_service_with_di._OAuthService__config_service.ACCESS_TOKEN_EXPIRE_MINUTES = (
                15
            )

            # Execute
            tokens = await oauth_service_with_di.issue_tokens(user)

            # Verify
            assert tokens.access_token == "test_access_token"
            assert tokens.refresh_token == "test_refresh_token"
            assert tokens.token_type == "bearer"

            # Verify the JWT utils were called
            mock_jwt_utils.create_access_token.assert_called_once()
            mock_jwt_utils.create_refresh_token.assert_called_once()
            from datetime import timedelta

            mock_refresh_token_repository.create_from_jti.assert_awaited_once_with(
                "test_jti", user.id, timedelta(days=7)
            )
            mock_audit.info.assert_called()

    @pytest.mark.asyncio
    async def test_authenticate_existing_account(
        self,
        oauth_service_with_di,
        mock_user_repository,
        mock_oauth_account_repository,
        mock_audit,
    ):
        """Test that authenticate_or_create returns existing user for existing OAuth account."""
        account = Mock(user_id=uuid.uuid4())
        mock_oauth_account_repository.get_by_provider_account = AsyncMock(
            return_value=account
        )
        existing_user = User(id=account.user_id, username="ex", email="ex@example.com")
        mock_user_repository.get_by_id = AsyncMock(return_value=existing_user)

        # Execute
        user = await oauth_service_with_di.authenticate_or_create(
            "github", "id123", "ex@example.com"
        )

        # Verify
        assert user == existing_user
        mock_oauth_account_repository.get_by_provider_account.assert_awaited_once_with(
            "github", "id123"
        )
        mock_user_repository.get_by_id.assert_awaited_once_with(account.user_id)
        mock_audit.info.assert_called()

    @pytest.mark.asyncio
    async def test_authenticate_link_missing_user(
        self,
        oauth_service_with_di,
        mock_user_repository,
        mock_oauth_account_repository,
        mock_audit,
    ):
        """Test that authenticate_or_create raises ValueError for missing user with existing OAuth account."""
        account = Mock(user_id=uuid.uuid4())
        mock_oauth_account_repository.get_by_provider_account = AsyncMock(
            return_value=account
        )
        mock_user_repository.get_by_id = AsyncMock(return_value=None)

        # Execute and verify
        with pytest.raises(ValueError):
            await oauth_service_with_di.authenticate_or_create("github", "id123", None)

        mock_user_repository.get_by_id.assert_awaited_once_with(account.user_id)
        mock_audit.error.assert_called()
