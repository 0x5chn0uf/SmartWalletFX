"""Test auth service registration functionality."""
from __future__ import annotations

from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security.roles import UserRole
from app.domain.schemas.user import UserCreate, WeakPasswordError
from app.models.user import User
from app.usecase.auth_usecase import DuplicateError


class TestAuthServiceRegistration:
    """Test auth service registration functionality."""

    @pytest.mark.asyncio
    async def test_register_success(self, auth_usecase, mock_user_repo):
        """Test successful user registration."""
        # Setup
        mock_user = User(
            id=1,
            username="test",
            email="test@example.com",
            roles=[UserRole.INDIVIDUAL_INVESTOR.value],
        )
        mock_user_repo.save.return_value = mock_user
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = None

        # Execute
        payload = UserCreate(
            username="test", email="test@example.com", password="StrongPass123!"
        )
        result = await auth_usecase.register(payload)

        # Verify
        assert result == mock_user
        mock_user_repo.get_by_username.assert_called_once_with("test")
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
        assert mock_user_repo.save.call_count == 1

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, auth_usecase, mock_user_repo):
        """Test registration with duplicate username."""
        mock_user_repo.get_by_username.return_value = Mock(spec=User)
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(DuplicateError) as exc_info:
            await auth_usecase.register(
                UserCreate(
                    username="test", email="test@example.com", password="StrongPass123!"
                )
            )
        assert exc_info.value.field == "username"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_usecase, mock_user_repo):
        """Test registration with duplicate email."""
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = Mock(spec=User)

        with pytest.raises(DuplicateError) as exc_info:
            await auth_usecase.register(
                UserCreate(
                    username="test", email="test@example.com", password="StrongPass123!"
                )
            )
        assert exc_info.value.field == "email"

    @pytest.mark.asyncio
    async def test_register_weak_password(self, auth_usecase):
        """Test registration with weak password."""
        with pytest.raises(WeakPasswordError):
            await auth_usecase.register(
                UserCreate(
                    username="test", email="test@example.com", password="weakpass"
                )  # 8 chars but no digit
            )

    @pytest.mark.asyncio
    async def test_register_integrity_error(self, auth_usecase, mock_user_repo):
        """Test handling of database integrity error."""
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.save.side_effect = IntegrityError(None, None, "users_email_key")

        with pytest.raises(DuplicateError) as exc_info:
            await auth_usecase.register(
                UserCreate(
                    username="test", email="test@example.com", password="StrongPass123!"
                )
            )
        assert exc_info.value.field == "email"

    @pytest.mark.asyncio
    async def test_register_duplicate_username_check_order(
        self, auth_usecase, mock_user_repo
    ):
        """Verify that username is checked before email for duplicates."""
        # Setup - make get_by_username return a user to trigger the duplicate check
        mock_user = Mock(spec=User)
        mock_user.username = "test"
        mock_user_repo.get_by_username.return_value = mock_user

        # Execute and expect DuplicateError
        with pytest.raises(DuplicateError, match="username"):
            await auth_usecase.register(
                UserCreate(
                    username="test", email="test@example.com", password="StrongPass123!"
                )
            )

        # Verify that get_by_username was called (which should happen first)
        mock_user_repo.get_by_username.assert_called_once_with("test")
        # get_by_email should not be called since username check failed first
        mock_user_repo.get_by_email.assert_not_called()
