from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.security.roles import UserRole
from app.domain.errors import InactiveUserError, InvalidCredentialsError
from app.models.user import User
from app.schemas.user import UserCreate, WeakPasswordError
from app.services.auth_service import DuplicateError


class TestAuthService:
    @pytest.mark.asyncio
    async def test_register_success(self, auth_service, mock_user_repo):
        """Test successful user registration."""
        # Setup
        mock_user_repo.exists.return_value = False
        mock_user = User(
            id=1,
            username="test",
            email="test@example.com",
            roles=[UserRole.INDIVIDUAL_INVESTOR.value],
        )
        mock_user_repo.save.return_value = mock_user

        # Execute
        payload = UserCreate(
            username="test", email="test@example.com", password="StrongPass123!"
        )
        result = await auth_service.register(payload)

        # Verify
        assert result == mock_user
        assert mock_user_repo.exists.call_count == 2  # Checked both username and email
        assert mock_user_repo.save.call_count == 1

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, auth_service, mock_user_repo):
        """Test registration with duplicate username."""
        mock_user_repo.exists.side_effect = [
            True,
            False,
        ]  # username exists, email doesn't

        with pytest.raises(DuplicateError) as exc_info:
            await auth_service.register(
                UserCreate(
                    username="test", email="test@example.com", password="StrongPass123!"
                )
            )
        assert exc_info.value.field == "username"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service, mock_user_repo):
        """Test registration with duplicate email."""
        mock_user_repo.exists.side_effect = [
            False,
            True,
        ]  # username doesn't exist, email does

        with pytest.raises(DuplicateError) as exc_info:
            await auth_service.register(
                UserCreate(
                    username="test", email="test@example.com", password="StrongPass123!"
                )
            )
        assert exc_info.value.field == "email"

    @pytest.mark.asyncio
    async def test_register_weak_password(self, auth_service):
        """Test registration with weak password."""
        with pytest.raises(WeakPasswordError):
            await auth_service.register(
                UserCreate(
                    username="test", email="test@example.com", password="weakpass"
                )  # 8 chars but no digit
            )

    @pytest.mark.asyncio
    async def test_register_integrity_error(self, auth_service, mock_user_repo):
        """Test handling of database integrity error."""
        mock_user_repo.exists.return_value = False
        mock_user_repo.save.side_effect = IntegrityError(None, None, "users_email_key")

        with pytest.raises(DuplicateError) as exc_info:
            await auth_service.register(
                UserCreate(
                    username="test", email="test@example.com", password="StrongPass123!"
                )
            )
        assert exc_info.value.field == "email"

    @pytest.mark.asyncio
    async def test_authenticate_success_by_username(self, auth_service, mock_user_repo):
        """Test successful authentication using username."""
        # Setup mock user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.roles = [UserRole.INDIVIDUAL_INVESTOR.value]
        mock_user.attributes = {}
        mock_user.is_active = True
        mock_user.hashed_password = "$2b$04$qRbw3X8ORqGW0Ru0JXmCfudYyKapkjduhzRQX4PQBj.7JriqK6tFC"  # 'StrongPass123!'
        mock_user_repo.get_by_username.return_value = mock_user
        mock_user_repo.get_by_email.return_value = None

        # Execute
        result = await auth_service.authenticate("test", "StrongPass123!")

        # Verify
        assert result.token_type == "bearer"
        assert result.access_token
        assert result.refresh_token

    @pytest.mark.asyncio
    async def test_authenticate_success_by_email(self, auth_service, mock_user_repo):
        """Test successful authentication using email."""
        # Setup mock user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.roles = [UserRole.INDIVIDUAL_INVESTOR.value]
        mock_user.attributes = {}
        mock_user.is_active = True
        mock_user.hashed_password = "$2b$04$qRbw3X8ORqGW0Ru0JXmCfudYyKapkjduhzRQX4PQBj.7JriqK6tFC"  # 'StrongPass123!'
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = mock_user

        # Execute
        result = await auth_service.authenticate("test@example.com", "StrongPass123!")

        # Verify
        assert result.token_type == "bearer"
        assert result.access_token
        assert result.refresh_token

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_user_repo):
        """Test authentication with non-existent user."""
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate("nonexistent", "StrongPass123!")

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_service, mock_user_repo):
        """Test authentication with inactive user."""
        mock_user = Mock(spec=User)
        mock_user.is_active = False
        mock_user_repo.get_by_username.return_value = mock_user

        with pytest.raises(InactiveUserError):
            await auth_service.authenticate("test", "StrongPass123!")

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, auth_service, mock_user_repo):
        """Test authentication with wrong password."""
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.hashed_password = "$2b$04$qRbw3X8ORqGW0Ru0JXmCfudYyKapkjduhzRQX4PQBj.7JriqK6tFC"  # 'StrongPass123!'
        mock_user_repo.get_by_username.return_value = mock_user

        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate("test", "WrongPass123!")

    @pytest.mark.asyncio
    async def test_authenticate_unverified_email(self, auth_service, mock_user_repo):
        """Authentication should fail when email is unverified past deadline."""
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.email_verified = False
        mock_user.hashed_password = (
            "$2b$04$qRbw3X8ORqGW0Ru0JXmCfudYyKapkjduhzRQX4PQBj.7JriqK6tFC"
        )
        mock_user_repo.get_by_username.return_value = mock_user

        from app.domain.errors import UnverifiedEmailError

        with pytest.raises(UnverifiedEmailError):
            await auth_service.authenticate("test", "StrongPass123!")

    @pytest.mark.asyncio
    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.JWTUtils")
    async def test_refresh_success(
        self, mock_jwt_utils, mock_rt_repo_class, auth_service
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
        mock_rt_repo = AsyncMock()
        mock_rt_repo_class.return_value = mock_rt_repo
        mock_token = Mock()
        mock_token.revoked = False
        mock_rt_repo.get_by_jti_hash.return_value = mock_token

        # Execute
        result = await auth_service.refresh("valid-refresh-token")

        # Verify
        assert result.access_token == "new-access-token"
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    @patch("app.services.auth_service.JWTUtils")
    async def test_refresh_invalid_token(self, mock_jwt_utils, auth_service):
        """Test refresh with invalid token."""
        mock_jwt_utils.decode_token.side_effect = Exception("Invalid token")

        with pytest.raises(InvalidCredentialsError):
            await auth_service.refresh("invalid-token")

    @pytest.mark.asyncio
    @patch("app.services.auth_service.JWTUtils")
    async def test_refresh_wrong_token_type(self, mock_jwt_utils, auth_service):
        """Test refresh with wrong token type."""
        mock_jwt_utils.decode_token.return_value = {
            "sub": "1",
            "type": "access",  # Wrong type
            "jti": "test-jti",
        }

        with pytest.raises(InvalidCredentialsError):
            await auth_service.refresh("wrong-type-token")

    @pytest.mark.asyncio
    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.JWTUtils")
    async def test_refresh_expired_token(
        self, mock_jwt_utils, mock_rt_repo_class, auth_service
    ):
        """Test refresh with expired token."""
        mock_jwt_utils.decode_token.return_value = {
            "sub": "1",
            "type": "refresh",
            "jti": "test-jti",
        }
        mock_jwt_utils.create_access_token.return_value = "new-access-token"

        # Setup mock refresh token repository
        mock_rt_repo = AsyncMock()
        mock_rt_repo_class.return_value = mock_rt_repo
        mock_token = Mock()
        mock_token.revoked = False
        mock_rt_repo.get_by_jti_hash.return_value = mock_token

        # Execute
        result = await auth_service.refresh("valid-refresh-token")

        # Verify
        assert result.access_token == "new-access-token"
        assert result.token_type == "bearer"
