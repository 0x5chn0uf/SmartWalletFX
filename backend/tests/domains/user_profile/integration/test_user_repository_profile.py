"""Integration tests for UserRepository profile management methods."""

import pytest


@pytest.mark.integration
class TestUserRepositoryProfile:
    """Test UserRepository profile management integration with database."""

    @pytest.mark.asyncio
    async def test_update_profile_database_persistence(
        self, user_repository_with_real_db, user_factory, db_session
    ):
        """Test profile updates persist to database correctly."""
        # Create a user
        user = await user_factory()
        await user_repository_with_real_db.save(user)

        # Update profile data
        profile_data = {
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Test bio",
            "timezone": "UTC",
            "preferred_currency": "EUR",
            "notification_preferences": {
                "email_notifications": True,
                "push_notifications": False,
            },
        }

        updated_user = await user_repository_with_real_db.update_profile(
            user, profile_data
        )

        # Verify updates
        assert updated_user.first_name == "John"
        assert updated_user.last_name == "Doe"
        assert updated_user.bio == "Test bio"
        assert updated_user.timezone == "UTC"
        assert updated_user.preferred_currency == "EUR"
        assert updated_user.notification_preferences["email_notifications"] is True

        # Verify persistence by fetching from database
        fetched_user = await user_repository_with_real_db.get_by_id(user.id)
        assert fetched_user.first_name == "John"
        assert fetched_user.notification_preferences["email_notifications"] is True

    @pytest.mark.asyncio
    async def test_update_profile_integrity_constraint(
        self, user_repository_with_real_db, user_factory
    ):
        """Test database integrity constraints for profile updates."""
        # Create two users
        user1 = await user_factory()
        user2 = await user_factory()

        await user_repository_with_real_db.save(user1)
        await user_repository_with_real_db.save(user2)

        # Try to update user2 with user1's email (should fail)
        with pytest.raises(Exception):  # IntegrityError from SQLAlchemy
            await user_repository_with_real_db.update_profile(
                user2, {"email": user1.email}
            )

    @pytest.mark.asyncio
    async def test_change_password_database_persistence(
        self, user_repository_with_real_db, user_factory
    ):
        """Test password changes persist to database correctly."""
        user = await user_factory()
        await user_repository_with_real_db.save(user)

        original_password = user.hashed_password
        new_hashed_password = "new_hashed_password_123"

        updated_user = await user_repository_with_real_db.change_password(
            user, new_hashed_password
        )

        # Verify password changed
        assert updated_user.hashed_password == new_hashed_password
        assert updated_user.hashed_password != original_password

        # Verify persistence
        fetched_user = await user_repository_with_real_db.get_by_id(user.id)
        assert fetched_user.hashed_password == new_hashed_password

    @pytest.mark.asyncio
    async def test_profile_fields_nullable(
        self, user_repository_with_real_db, user_factory
    ):
        """Test that new profile fields accept null values."""
        user = await user_factory(
            first_name=None,
            last_name=None,
            bio=None,
            timezone=None,
            profile_picture_url=None,
            notification_preferences=None,
        )

        saved_user = await user_repository_with_real_db.save(user)

        # All profile fields should be None
        assert saved_user.first_name is None
        assert saved_user.last_name is None
        assert saved_user.bio is None
        assert saved_user.timezone is None
        assert saved_user.profile_picture_url is None
        assert saved_user.notification_preferences is None

    @pytest.mark.asyncio
    async def test_notification_preferences_json_storage(
        self, user_repository_with_real_db, user_factory
    ):
        """Test JSON storage and retrieval of notification preferences."""
        complex_preferences = {
            "email_notifications": True,
            "push_notifications": False,
            "sms_notifications": True,
            "price_alerts": {
                "enabled": True,
                "threshold_percentage": 5.0,
                "currencies": ["BTC", "ETH"],
            },
            "portfolio_alerts": {"daily_summary": True, "weekly_report": False},
        }

        user = await user_factory(
            notification_preferences=complex_preferences,
        )

        saved_user = await user_repository_with_real_db.save(user)

        # Verify complex JSON structure is preserved
        assert saved_user.notification_preferences["email_notifications"] is True
        assert (
            saved_user.notification_preferences["price_alerts"]["threshold_percentage"]
            == 5.0
        )
        assert (
            "BTC" in saved_user.notification_preferences["price_alerts"]["currencies"]
        )

        # Verify after fetching from database
        fetched_user = await user_repository_with_real_db.get_by_id(user.id)
        assert fetched_user.notification_preferences == complex_preferences

    @pytest.mark.asyncio
    async def test_profile_update_partial_fields(
        self, user_repository_with_real_db, user_factory
    ):
        """Test updating only specific profile fields."""
        user = await user_factory(
            first_name="Original",
            last_name="Name",
            bio="Original bio",
        )
        await user_repository_with_real_db.save(user)

        # Update only first name and bio
        partial_update = {"first_name": "Updated", "bio": "Updated bio"}

        updated_user = await user_repository_with_real_db.update_profile(
            user, partial_update
        )

        # Only specified fields should change
        assert updated_user.first_name == "Updated"
        assert updated_user.bio == "Updated bio"
        assert updated_user.last_name == "Name"  # Unchanged
        assert updated_user.username == user.username  # Unchanged
