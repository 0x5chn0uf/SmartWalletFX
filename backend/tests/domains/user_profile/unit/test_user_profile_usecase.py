"""Unit tests for UserProfileUsecase."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.errors import InvalidCredentialsError
from app.domain.schemas.user import (
    PasswordChange,
    UserProfileRead,
    UserProfileUpdate,
)
from app.models.user import User
from app.usecase.user_profile_usecase import (
    ProfileUpdateError,
    UserProfileUsecase,
)
from app.utils import security


class TestUserProfileUsecase:
    """Test UserProfileUsecase business logic."""

    @pytest.fixture
    def mock_user_repo(self):
        """Mock UserRepository for testing."""
        return AsyncMock()

    @pytest.fixture
    def mock_audit(self):
        """Mock Audit for testing."""
        return Mock()

    @pytest.fixture
    def usecase(self, mock_user_repo, mock_audit):
        """UserProfileUsecase instance for testing."""
        return UserProfileUsecase(mock_user_repo, mock_audit)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_profile_success(
        self, usecase, mock_user_repo, user_with_profile_data
    ):
        """Test successfully retrieving user profile by ID."""
        mock_user_repo.get_by_id.return_value = user_with_profile_data

        result = await usecase.get_profile("user-123")

        assert isinstance(result, UserProfileRead)
        assert result.username == "profile_user"
        assert result.email == "profile@example.com"
        mock_user_repo.get_by_id.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_profile_user_not_found(self, usecase, mock_user_repo):
        """Test get_profile returns None when user doesn't exist."""
        mock_user_repo.get_by_id.return_value = None

        result = await usecase.get_profile("nonexistent-user")

        assert result is None
        mock_user_repo.get_by_id.assert_called_once_with("nonexistent-user")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_profile_success(
        self,
        usecase,
        mock_user_repo,
        user_profile_update_schema,
    ):
        """Test updating profile with valid data."""
        # Create a proper User object for the test
        test_user = User(
            id=uuid.uuid4(),
            username="profile_user",
            email="profile@example.com",
            hashed_password="hashed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            email_verified=True,
        )

        mock_user_repo.get_by_id.return_value = test_user
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.update_profile.return_value = test_user

        result = await usecase.update_profile("user-123", user_profile_update_schema)

        assert isinstance(result, UserProfileRead)
        mock_user_repo.update_profile.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_profile_username_conflict(
        self, usecase, mock_user_repo, user_with_profile_data, user_factory
    ):
        """Test update_profile raises ProfileUpdateError for duplicate username."""
        mock_user_repo.get_by_id.return_value = user_with_profile_data
        # Mock another user with the same username
        conflicting_user = await user_factory(username="updated_user")
        mock_user_repo.get_by_username.return_value = conflicting_user

        profile_update = UserProfileUpdate(username="updated_user")

        with pytest.raises(ProfileUpdateError) as exc_info:
            await usecase.update_profile("user-123", profile_update)

        assert exc_info.value.field == "username"
        assert "already taken" in exc_info.value.message

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_profile_email_conflict(
        self, usecase, mock_user_repo, user_with_profile_data, user_factory
    ):
        """Test update_profile raises ProfileUpdateError for duplicate email."""
        mock_user_repo.get_by_id.return_value = user_with_profile_data
        mock_user_repo.get_by_username.return_value = None
        # Mock another user with the same email
        conflicting_user = await user_factory(email="updated@example.com")
        mock_user_repo.get_by_email.return_value = conflicting_user

        profile_update = UserProfileUpdate(email="updated@example.com")

        with pytest.raises(ProfileUpdateError) as exc_info:
            await usecase.update_profile("user-123", profile_update)

        assert exc_info.value.field == "email"
        assert "already registered" in exc_info.value.message

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_profile_user_not_found(
        self, usecase, mock_user_repo, user_profile_update_schema
    ):
        """Test update_profile raises ProfileUpdateError when user doesn't exist."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(ProfileUpdateError) as exc_info:
            await usecase.update_profile("nonexistent-user", user_profile_update_schema)

        assert exc_info.value.field == "user"
        assert "not found" in exc_info.value.message

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_change_password_success(
        self,
        usecase,
        mock_user_repo,
        user_with_profile_data,
        password_change_schema,
        monkeypatch,
    ):
        """Test changing password with valid current password."""
        # Mock password verification
        monkeypatch.setattr(security, "verify_password", lambda plain, hashed: True)
        monkeypatch.setattr(
            security, "get_password_hash", lambda password: f"hashed_{password}"
        )

        mock_user_repo.get_by_id.return_value = user_with_profile_data
        mock_user_repo.change_password.return_value = user_with_profile_data

        result = await usecase.change_password("user-123", password_change_schema)

        assert result is True
        mock_user_repo.change_password.assert_called_once_with(
            user_with_profile_data, "hashed_NewSecurePassword456!"
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_change_password_invalid_current(
        self,
        usecase,
        mock_user_repo,
        user_with_profile_data,
        password_change_schema,
        monkeypatch,
    ):
        """Test change_password raises InvalidCredentialsError for wrong current password."""
        # Mock password verification to fail
        monkeypatch.setattr(security, "verify_password", lambda plain, hashed: False)

        mock_user_repo.get_by_id.return_value = user_with_profile_data

        with pytest.raises(InvalidCredentialsError) as exc_info:
            await usecase.change_password("user-123", password_change_schema)

        assert "Current password is incorrect" in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_change_password_user_not_found(
        self, usecase, mock_user_repo, password_change_schema
    ):
        """Test change_password raises InvalidCredentialsError when user doesn't exist."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(InvalidCredentialsError) as exc_info:
            await usecase.change_password("nonexistent-user", password_change_schema)

        assert "User not found" in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_account_success(
        self, usecase, mock_user_repo, user_with_profile_data
    ):
        """Test successfully deleting user account."""
        mock_user_repo.get_by_id.return_value = user_with_profile_data
        mock_user_repo.delete.return_value = None

        result = await usecase.delete_account("user-123")

        assert result is True
        mock_user_repo.delete.assert_called_once_with(user_with_profile_data)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_account_user_not_found(self, usecase, mock_user_repo):
        """Test delete_account returns False when user doesn't exist."""
        mock_user_repo.get_by_id.return_value = None

        result = await usecase.delete_account("nonexistent-user")

        assert result is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_notification_preferences_success(
        self,
        usecase,
        mock_user_repo,
        user_with_profile_data,
        notification_preferences_data,
    ):
        """Test updating notification preferences."""
        mock_user_repo.get_by_id.return_value = user_with_profile_data
        mock_user_repo.update_profile.return_value = user_with_profile_data

        result = await usecase.update_notification_preferences(
            "user-123", notification_preferences_data
        )

        assert isinstance(result, UserProfileRead)
        mock_user_repo.update_profile.assert_called_once()
        # Verify the preferences were passed correctly
        call_args = mock_user_repo.update_profile.call_args[0]
        update_data = call_args[1]
        assert update_data["notification_preferences"] == notification_preferences_data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_notification_preferences_invalid_keys(
        self, usecase, mock_user_repo, user_with_profile_data
    ):
        """Test update_notification_preferences raises ProfileUpdateError for invalid preference keys."""
        mock_user_repo.get_by_id.return_value = user_with_profile_data

        invalid_preferences = {"invalid_key": True, "email_notifications": False}

        with pytest.raises(ProfileUpdateError) as exc_info:
            await usecase.update_notification_preferences(
                "user-123", invalid_preferences
            )

        assert exc_info.value.field == "preferences"
        assert "Invalid notification preference keys" in exc_info.value.message
