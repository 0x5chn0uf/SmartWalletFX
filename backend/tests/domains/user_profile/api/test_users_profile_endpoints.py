"""API tests for user profile management endpoints."""
from unittest.mock import patch

import pytest
from fastapi import status


def store_user_data_for_mock(user):
    """Store user data for mock system to access."""
    import tests.conftest as conftest_module

    conftest_module._test_user_data = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "bio": user.bio,
        "timezone": user.timezone,
        "preferred_currency": user.preferred_currency,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "email_verified": user.email_verified,
    }


@pytest.mark.integration
class TestUserProfileEndpoints:
    """Test user profile management API endpoints."""

    @pytest.mark.asyncio
    async def test_get_user_profile_success(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test GET /users/me/profile returns profile data."""
        # Create user with profile data
        user = await user_factory(
            username="profile_user",
            email="profile@example.com",
            first_name="Jane",
            last_name="Smith",
            bio="Test bio",
            timezone="UTC",
            preferred_currency="USD",
        )

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.get(
                "/users/me/profile", headers=auth_headers
            )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["username"] == "profile_user"
        assert data["email"] == "profile@example.com"
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
        assert data["bio"] == "Test bio"
        assert data["timezone"] == "UTC"
        assert data["preferred_currency"] == "USD"

    @pytest.mark.asyncio
    async def test_get_user_profile_unauthorized(self, integration_async_client):
        """Test GET /users/me/profile returns 401 without authentication."""
        response = await integration_async_client.get("/users/me/profile")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_update_user_profile_success(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test PUT /users/me/profile updates profile successfully."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        update_data = {
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Updated bio",
            "timezone": "America/New_York",
            "preferred_currency": "EUR",
        }

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.put(
                "/users/me/profile", headers=auth_headers, json=update_data
            )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["bio"] == "Updated bio"
        assert data["timezone"] == "America/New_York"
        assert data["preferred_currency"] == "EUR"

    @pytest.mark.asyncio
    async def test_update_user_profile_validation_error(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test PUT /users/me/profile returns 400 for invalid data."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        invalid_data = {"email": "invalid-email-format", "username": "ab"}  # Too short

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.put(
                "/users/me/profile", headers=auth_headers, json=invalid_data
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_user_profile_username_conflict(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test PUT /users/me/profile returns 400 for duplicate username."""
        existing_user = await user_factory(email="user1@example.com")
        user2 = await user_factory(email="user2@example.com")

        # Store user data for mock to access
        store_user_data_for_mock(user2)

        # Store existing usernames for conflict detection
        import tests.conftest as conftest_module

        if not hasattr(conftest_module, "_existing_usernames"):
            conftest_module._existing_usernames = set()
        conftest_module._existing_usernames.add(existing_user.username)

        # Get auth headers for user2
        auth_headers = await get_auth_headers_for_user_factory(user2)

        update_data = {"username": existing_user.username}

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user2.id
        ):
            response = await integration_async_client.put(
                "/users/me/profile", headers=auth_headers, json=update_data
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already taken" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test POST /users/me/change-password changes password successfully."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        password_data = {
            "current_password": "OldPassword123!",
            "new_password": "NewSecurePassword456!",
        }

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.post(
                "/users/me/change-password", headers=auth_headers, json=password_data
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_change_password_invalid_current(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test POST /users/me/change-password returns 400 for incorrect current password."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewSecurePassword456!",
        }

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.post(
                "/users/me/change-password", headers=auth_headers, json=password_data
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Current password is incorrect" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test POST /users/me/change-password returns 422 for weak new password."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        password_data = {"current_password": "OldPassword123!", "new_password": "weak"}

        response = await integration_async_client.post(
            "/users/me/change-password", headers=auth_headers, json=password_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_notification_preferences_success(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test PUT /users/me/notifications updates preferences successfully."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        preferences = {
            "email_notifications": True,
            "push_notifications": False,
            "price_alerts": True,
            "portfolio_alerts": False,
            "security_alerts": True,
        }

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.put(
                "/users/me/notifications", headers=auth_headers, json=preferences
            )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["notification_preferences"]["email_notifications"] is True
        assert data["notification_preferences"]["push_notifications"] is False

    @pytest.mark.asyncio
    async def test_update_notification_preferences_invalid(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test PUT /users/me/notifications returns 400 for invalid preferences."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        invalid_preferences = {"invalid_key": True, "email_notifications": False}

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.put(
                "/users/me/notifications",
                headers=auth_headers,
                json=invalid_preferences,
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid notification preference keys" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_current_user_account_success(
        self, integration_async_client, get_auth_headers_for_user_factory, user_factory
    ):
        """Test DELETE /users/me deletes account successfully."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.delete(
                "/users/me", headers=auth_headers
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_upload_profile_picture_success(
        self,
        integration_async_client,
        get_auth_headers_for_user_factory,
        user_factory,
        valid_image_file,
    ):
        """Test POST /users/me/profile/picture uploads image successfully."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.post(
                "/users/me/profile/picture",
                headers=auth_headers,
                files={"file": ("test.jpg", valid_image_file.file, "image/jpeg")},
            )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "profile_picture_url" in data
        assert data["message"] == "Profile picture uploaded successfully"
        assert data["profile_picture_url"].endswith(".jpg")

    @pytest.mark.asyncio
    async def test_upload_profile_picture_invalid_file(
        self,
        integration_async_client,
        get_auth_headers_for_user_factory,
        user_factory,
        invalid_image_file,
    ):
        """Test POST /users/me/profile/picture returns 400 for invalid file types."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.post(
                "/users/me/profile/picture",
                headers=auth_headers,
                files={"file": ("test.txt", invalid_image_file.file, "text/plain")},
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "File type not allowed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_profile_picture_too_large(
        self,
        integration_async_client,
        get_auth_headers_for_user_factory,
        user_factory,
        large_image_file,
    ):
        """Test POST /users/me/profile/picture returns 400 for oversized files."""
        user = await user_factory()

        # Store user data for mock to access
        store_user_data_for_mock(user)

        # Get auth headers for the user
        auth_headers = await get_auth_headers_for_user_factory(user)

        with patch(
            "app.api.dependencies.get_user_id_from_request", return_value=user.id
        ):
            response = await integration_async_client.post(
                "/users/me/profile/picture",
                headers=auth_headers,
                files={"file": ("large.jpg", large_image_file.file, "image/jpeg")},
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "File too large" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_profile_endpoints_require_authentication(
        self, integration_async_client
    ):
        """Test all profile endpoints require authentication."""
        endpoints = [
            ("GET", "/users/me/profile"),
            ("PUT", "/users/me/profile"),
            ("POST", "/users/me/change-password"),
            ("PUT", "/users/me/notifications"),
            ("DELETE", "/users/me"),
            ("POST", "/users/me/profile/picture"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = await integration_async_client.get(endpoint)
            elif method == "PUT":
                response = await integration_async_client.put(endpoint, json={})
            elif method == "POST":
                response = await integration_async_client.post(endpoint, json={})
            elif method == "DELETE":
                response = await integration_async_client.delete(endpoint)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
