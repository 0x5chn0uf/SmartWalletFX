"""Shared fixtures for user profile management tests."""
import io

import pytest
from fastapi import UploadFile

from app.domain.schemas.user import PasswordChange, UserProfileUpdate


@pytest.fixture
def profile_update_data():
    """Sample UserProfileUpdate data for testing."""
    return {
        "username": "updated_user",
        "email": "updated@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "Updated bio description",
        "timezone": "UTC",
        "preferred_currency": "USD",
        "notification_preferences": {
            "email_notifications": True,
            "push_notifications": False,
            "price_alerts": True,
            "portfolio_alerts": True,
            "security_alerts": True,
        },
    }


@pytest.fixture
def password_change_data():
    """Sample PasswordChange data for testing."""
    return {
        "current_password": "OldPassword123!",
        "new_password": "NewSecurePassword456!",
    }


@pytest.fixture
def notification_preferences_data():
    """Sample notification preferences for testing."""
    return {
        "email_notifications": True,
        "push_notifications": False,
        "sms_notifications": True,
        "price_alerts": True,
        "portfolio_alerts": False,
        "security_alerts": True,
    }


@pytest.fixture
def valid_image_file():
    """Mock valid image UploadFile for testing."""
    file_content = b"fake_image_content"
    file_obj = io.BytesIO(file_content)

    return UploadFile(
        filename="test_image.jpg",
        file=file_obj,
        size=len(file_content),
        headers={"content-type": "image/jpeg"},
    )


@pytest.fixture
def invalid_image_file():
    """Mock invalid UploadFile for testing."""
    file_content = b"fake_text_content"
    file_obj = io.BytesIO(file_content)

    return UploadFile(
        filename="test_file.txt",
        file=file_obj,
        size=len(file_content),
        headers={"content-type": "text/plain"},
    )


@pytest.fixture
def large_image_file():
    """Mock oversized image UploadFile for testing."""
    # Create a file larger than 5MB
    file_content = b"x" * (6 * 1024 * 1024)  # 6MB
    file_obj = io.BytesIO(file_content)

    return UploadFile(
        filename="large_image.jpg",
        file=file_obj,
        size=len(file_content),
        headers={"content-type": "image/jpeg"},
    )


@pytest.fixture
def user_profile_update_schema(profile_update_data):
    """UserProfileUpdate schema instance for testing."""
    return UserProfileUpdate(**profile_update_data)


@pytest.fixture
def password_change_schema(password_change_data):
    """PasswordChange schema instance for testing."""
    return PasswordChange(**password_change_data)


@pytest.fixture
def user_with_profile_data():
    """User profile data for testing without database dependency."""
    from datetime import datetime
    from uuid import UUID

    from app.models.user import User

    user = User(
        id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        username="profile_user",
        email="profile@example.com",
        hashed_password="hashed_test_password",
        email_verified=True,
        first_name="Jane",
        last_name="Smith",
        bio="Test user bio",
        timezone="America/New_York",
        preferred_currency="EUR",
        profile_picture_url="http://example.com/profile.jpg",
        notification_preferences={
            "email_notifications": True,
            "push_notifications": True,
            "price_alerts": False,
            "portfolio_alerts": True,
            "security_alerts": True,
        },
        created_at=datetime.fromisoformat("2023-01-01T00:00:00+00:00"),
        updated_at=datetime.fromisoformat("2023-01-01T00:00:00+00:00"),
        roles=["individual_investor"],
        attributes={},
    )
    return user
