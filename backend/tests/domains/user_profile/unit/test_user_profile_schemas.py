"""Unit tests for user profile schemas."""
import pytest
from pydantic import ValidationError

from app.domain.schemas.user import (
    PasswordChange,
    UserProfileRead,
    UserProfileUpdate,
    WeakPasswordError,
)


class TestUserProfileUpdate:
    """Test UserProfileUpdate schema validation."""

    @pytest.mark.unit
    def test_user_profile_update_valid_data(self, profile_update_data):
        """Test UserProfileUpdate with valid data."""
        schema = UserProfileUpdate(**profile_update_data)

        assert schema.username == "updated_user"
        assert schema.email == "updated@example.com"
        assert schema.first_name == "John"
        assert schema.last_name == "Doe"
        assert schema.bio == "Updated bio description"
        assert schema.timezone == "UTC"
        assert schema.preferred_currency == "USD"
        assert schema.notification_preferences["email_notifications"] is True

    @pytest.mark.unit
    def test_user_profile_update_invalid_email(self):
        """Test UserProfileUpdate rejects invalid email formats."""
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(email="invalid-email")

        assert "value is not a valid email address" in str(exc_info.value)

    @pytest.mark.unit
    def test_user_profile_update_username_length_validation(self):
        """Test UserProfileUpdate validates username length constraints."""
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(username="ab")
        assert "at least 3 characters" in str(exc_info.value)

        # Too long
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(username="x" * 51)
        assert "at most 50 characters" in str(exc_info.value)

    @pytest.mark.unit
    def test_user_profile_update_optional_fields(self):
        """Test UserProfileUpdate handles optional fields correctly."""
        # Test with minimal data
        schema = UserProfileUpdate(username="testuser")
        assert schema.username == "testuser"
        assert schema.email is None
        assert schema.first_name is None

        # Test with empty data
        schema = UserProfileUpdate()
        assert schema.username is None
        assert schema.email is None

    @pytest.mark.unit
    def test_user_profile_update_field_length_limits(self):
        """Test UserProfileUpdate field length validation."""
        # Bio too long
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(bio="x" * 1001)
        assert "at most 1000 characters" in str(exc_info.value)

        # First name too long
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(first_name="x" * 101)
        assert "at most 100 characters" in str(exc_info.value)


class TestPasswordChange:
    """Test PasswordChange schema validation."""

    @pytest.mark.unit
    def test_password_change_valid_data(self, password_change_data):
        """Test PasswordChange with valid strong passwords."""
        schema = PasswordChange(**password_change_data)

        assert schema.current_password == "OldPassword123!"
        assert schema.new_password == "NewSecurePassword456!"

    @pytest.mark.unit
    def test_password_change_weak_password(self):
        """Test PasswordChange rejects weak passwords."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            PasswordChange(current_password="OldPassword123!", new_password="weak")

        assert "strength requirements" in str(exc_info.value)

    @pytest.mark.unit
    def test_password_change_missing_fields(self):
        """Test PasswordChange requires both password fields."""
        with pytest.raises(ValidationError):
            PasswordChange(current_password="OldPassword123!")

        with pytest.raises(ValidationError):
            PasswordChange(new_password="NewPassword123!")

    @pytest.mark.unit
    def test_password_change_empty_passwords(self):
        """Test PasswordChange rejects empty passwords."""
        with pytest.raises(ValidationError):
            PasswordChange(current_password="", new_password="NewPassword123!")


class TestUserProfileRead:
    """Test UserProfileRead schema serialization."""

    @pytest.mark.unit
    def test_user_profile_read_serialization(self, user_with_profile_data):
        """Test UserProfileRead model serialization."""
        schema = UserProfileRead.model_validate(user_with_profile_data)

        assert schema.username == "profile_user"
        assert schema.email == "profile@example.com"
        assert schema.first_name == "Jane"
        assert schema.last_name == "Smith"
        assert schema.bio == "Test user bio"
        assert schema.timezone == "America/New_York"
        assert schema.preferred_currency == "EUR"
        assert schema.profile_picture_url == "http://example.com/profile.jpg"
        assert schema.notification_preferences["email_notifications"] is True

    @pytest.mark.unit
    def test_user_profile_read_with_none_values(self):
        """Test UserProfileRead handles None values correctly."""
        user_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "test_user",
            "email": "test@example.com",
            "first_name": None,
            "last_name": None,
            "bio": None,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "email_verified": True,
        }

        schema = UserProfileRead.model_validate(user_data)
        assert schema.username == "test_user"
        assert schema.first_name is None
        assert schema.last_name is None
        assert schema.bio is None
