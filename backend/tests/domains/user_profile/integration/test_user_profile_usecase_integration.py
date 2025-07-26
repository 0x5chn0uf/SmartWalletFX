"""Integration tests for UserProfileUsecase with real dependencies."""
import pytest

from app.domain.schemas.user import PasswordChange, UserProfileUpdate
from app.usecase.user_profile_usecase import (
    ProfileUpdateError,
    UserProfileUsecase,
)
from app.utils import security


@pytest.mark.integration
class TestUserProfileUsecaseIntegration:
    """Test UserProfileUsecase integration with real repository and database."""

    @pytest.fixture
    def usecase(self, user_repository_with_real_db, mock_audit):
        """UserProfileUsecase with real dependencies."""
        return UserProfileUsecase(user_repository_with_real_db, mock_audit)

    @pytest.mark.asyncio
    async def test_profile_workflow_end_to_end(self, usecase, user_factory):
        """Test complete profile update workflow end-to-end."""
        # Create user
        user = await user_factory()
        await usecase._UserProfileUsecase__user_repo.save(user)
        user_id = str(user.id)

        # Get initial profile
        initial_profile = await usecase.get_profile(user_id)
        assert initial_profile.username == user.username
        assert initial_profile.first_name is None

        # Update profile
        profile_update = UserProfileUpdate(
            first_name="John",
            last_name="Doe",
            bio="Test user bio",
            timezone="America/New_York",
            preferred_currency="USD",
            notification_preferences={
                "email_notifications": True,
                "push_notifications": False,
            },
        )

        updated_profile = await usecase.update_profile(user_id, profile_update)

        # Verify updates
        assert updated_profile.first_name == "John"
        assert updated_profile.last_name == "Doe"
        assert updated_profile.bio == "Test user bio"
        assert updated_profile.timezone == "America/New_York"
        assert updated_profile.preferred_currency == "USD"
        assert updated_profile.notification_preferences["email_notifications"] is True

        # Get profile again to verify persistence
        final_profile = await usecase.get_profile(user_id)
        assert final_profile.first_name == "John"
        assert final_profile.notification_preferences["email_notifications"] is True

    @pytest.mark.asyncio
    async def test_password_change_with_profile_update(self, usecase, user_factory):
        """Test password change combined with profile updates."""
        # Create user with known password
        hashed_password = security.get_password_hash("OldPassword123!")
        user = await user_factory(
            hashed_password=hashed_password,
        )
        await usecase._UserProfileUsecase__user_repo.save(user)
        user_id = str(user.id)

        # Change password
        password_change = PasswordChange(
            current_password="OldPassword123!", new_password="NewSecurePassword456!"
        )

        result = await usecase.change_password(user_id, password_change)
        assert result is True

        # Update profile after password change
        profile_update = UserProfileUpdate(first_name="John")
        updated_profile = await usecase.update_profile(user_id, profile_update)
        assert updated_profile.first_name == "John"

        # Verify user can't use old password for future changes
        old_password_change = PasswordChange(
            current_password="OldPassword123!",  # Old password
            new_password="AnotherPassword789!",
        )

        with pytest.raises(Exception):  # Should fail with old password
            await usecase.change_password(user_id, old_password_change)

    @pytest.mark.asyncio
    async def test_account_deletion_cascades(self, usecase, user_factory):
        """Test that account deletion properly cleans up related data."""
        # Create user with profile data
        user = await user_factory(
            first_name="John",
            bio="Test bio",
            notification_preferences={"email_notifications": True},
        )
        await usecase._UserProfileUsecase__user_repo.save(user)
        user_id = str(user.id)

        # Verify user exists with profile data
        profile = await usecase.get_profile(user_id)
        assert profile is not None
        assert profile.first_name == "John"

        # Delete account
        result = await usecase.delete_account(user_id)
        assert result is True

        # Verify user and all profile data are gone
        deleted_profile = await usecase.get_profile(user_id)
        assert deleted_profile is None

    @pytest.mark.asyncio
    async def test_concurrent_profile_updates(self, usecase, user_factory):
        """Test handling of concurrent profile updates."""
        # Create user
        user = await user_factory()
        await usecase._UserProfileUsecase__user_repo.save(user)
        user_id = str(user.id)

        # Simulate concurrent updates to different fields
        update1 = UserProfileUpdate(first_name="John")
        update2 = UserProfileUpdate(last_name="Doe")

        # Both updates should succeed
        result1 = await usecase.update_profile(user_id, update1)
        result2 = await usecase.update_profile(user_id, update2)

        assert result1.first_name == "John"
        assert result2.last_name == "Doe"

        # Final state should have both changes
        final_profile = await usecase.get_profile(user_id)
        assert final_profile.first_name == "John"
        assert final_profile.last_name == "Doe"

    @pytest.mark.asyncio
    async def test_username_conflict_prevention(self, usecase, user_factory):
        """Test prevention of username conflicts across users."""
        # Create two users
        user1 = await user_factory()
        user2 = await user_factory()

        await usecase._UserProfileUsecase__user_repo.save(user1)
        await usecase._UserProfileUsecase__user_repo.save(user2)

        user2_id = str(user2.id)

        # Try to update user2's username to user1's username
        profile_update = UserProfileUpdate(username=user1.username)

        with pytest.raises(ProfileUpdateError) as exc_info:
            await usecase.update_profile(user2_id, profile_update)

        assert exc_info.value.field == "username"
        assert "already taken" in exc_info.value.message

        # Verify user2's username unchanged
        user2_profile = await usecase.get_profile(user2_id)
        assert user2_profile.username == user2.username
