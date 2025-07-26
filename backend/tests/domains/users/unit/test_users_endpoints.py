"""
Tests for users endpoints using dependency injection pattern.

This module tests the Users endpoint class that uses the singleton
pattern with dependency injection.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, Request, status

from app.domain.schemas.user import UserCreate, UserProfileUpdate, UserRead
from app.models.user import User
from app.services.file_upload_service import FileUploadError
from app.usecase.user_profile_usecase import ProfileUpdateError


@pytest.mark.unit
@pytest.mark.asyncio
async def test_read_current_user_success(users_endpoint_with_di):
    """Test successful reading of current user."""
    endpoint = users_endpoint_with_di

    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )
    # Add is_active attribute dynamically
    setattr(user, "is_active", True)

    # Mock the get_user_id_from_request function and user repository
    with patch(
        "app.api.endpoints.users.get_user_id_from_request"
    ) as mock_get_user_id, patch("app.api.endpoints.users.Audit") as mock_audit:
        mock_get_user_id.return_value = user.id
        endpoint._Users__user_repo.get_by_id.return_value = user

        # Execute
        result = await endpoint.read_current_user(request)

        # Assert
        assert isinstance(result, User)
        assert result.id == user.id
        assert result.username == user.username
        assert result.email == user.email
        mock_get_user_id.assert_called_once_with(request)
        endpoint._Users__user_repo.get_by_id.assert_awaited_once_with(user.id)
        mock_audit.info.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_read_current_user_inactive(users_endpoint_with_di):
    """Test reading current user when user is inactive."""
    endpoint = users_endpoint_with_di

    # Setup
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )
    # Add is_active attribute dynamically as False
    setattr(user, "is_active", False)

    # Mock the get_user_id_from_request function and user repository
    with patch("app.api.endpoints.users.get_user_id_from_request") as mock_get_user_id:
        mock_get_user_id.return_value = user.id
        endpoint._Users__user_repo.get_by_id.return_value = user

        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await endpoint.read_current_user(request)

        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == "Inactive or disabled user account"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_user_success(users_endpoint_with_di):
    """Test successful user update."""
    endpoint = users_endpoint_with_di

    # Setup
    user_id = uuid.uuid4()
    current_user = User(
        id=user_id,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    # Create updated user
    updated_user = User(
        id=user_id,
        username="updated_user",
        email="updated@example.com",
        hashed_password="hashed",
    )

    # Mock repository methods
    endpoint._Users__user_repo.get_by_id.return_value = current_user
    endpoint._Users__user_repo.update.return_value = updated_user

    user_in = UserCreate(
        username="updated_user",
        email="updated@example.com",
        password="StrongP@ss123",
    )

    # Mock request and dependencies
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    with patch("app.api.endpoints.users.get_user_id_from_request") as mock_get_user_id:
        mock_get_user_id.return_value = user_id

        # Execute - correct parameter order: (request, user_id, user_in)
        result = await endpoint.update_user(request, user_id, user_in)

        # Assert
        assert result == updated_user
        endpoint._Users__user_repo.get_by_id.assert_awaited_once_with(user_id)
        endpoint._Users__user_repo.update.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_user_not_found(users_endpoint_with_di):
    """Test updating user when user is not found."""
    endpoint = users_endpoint_with_di

    # Setup
    user_id = uuid.uuid4()
    current_user = User(
        id=uuid.uuid4(),  # Different ID
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    # Mock repository to return None
    endpoint._Users__user_repo.get_by_id.return_value = None

    user_in = UserCreate(
        username="updated_user",
        email="updated@example.com",
        password="StrongP@ss123",
    )

    # Mock request
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    with patch("app.api.endpoints.users.get_user_id_from_request") as mock_get_user_id:
        mock_get_user_id.return_value = current_user.id

        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await endpoint.update_user(request, user_id, user_in)

        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert excinfo.value.detail == "User not found"
        endpoint._Users__user_repo.get_by_id.assert_awaited_once_with(user_id)
        endpoint._Users__user_repo.update.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_user_unauthorized(
    users_endpoint_with_di,
    mock_user_repository,
):
    """Test updating user when not authorized using regular mocks."""
    endpoint = users_endpoint_with_di

    # Setup test data
    user_id = uuid.uuid4()
    db_user = User(
        id=user_id,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    current_user = User(
        id=uuid.uuid4(),  # Different ID - unauthorized
        username="otheruser",
        email="other@example.com",
        hashed_password="hashed",
    )

    # Configure mock for authorization failure scenario
    mock_user_repository.get_by_id = AsyncMock(return_value=db_user)

    user_in = UserCreate(
        username="updated_user",
        email="updated@example.com",
        password="StrongP@ss123",
    )

    # Mock request
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    with patch("app.api.endpoints.users.get_user_id_from_request") as mock_get_user_id:
        mock_get_user_id.return_value = current_user.id

        # Execute and Assert authorization failure
        with pytest.raises(HTTPException) as excinfo:
            await endpoint.update_user(request, user_id, user_in)

        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == "Not authorized"
        endpoint._Users__user_repo.get_by_id.assert_awaited_once_with(user_id)
        endpoint._Users__user_repo.update.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_user_success(users_endpoint_with_di):
    """Test successful user deletion."""
    endpoint = users_endpoint_with_di

    # Setup
    user_id = uuid.uuid4()
    current_user = User(
        id=user_id,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    # Mock repository methods
    endpoint._Users__user_repo.get_by_id.return_value = current_user
    endpoint._Users__user_repo.delete.return_value = None

    # Mock request
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    with patch("app.api.endpoints.users.get_user_id_from_request") as mock_get_user_id:
        mock_get_user_id.return_value = user_id

        # Execute
        result = await endpoint.delete_user(request, user_id)

        # Assert
        assert result is None
        endpoint._Users__user_repo.get_by_id.assert_awaited_once_with(user_id)
        endpoint._Users__user_repo.delete.assert_awaited_once_with(current_user)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_user_not_found(users_endpoint_with_di):
    """Test deleting user when user is not found."""
    endpoint = users_endpoint_with_di

    # Setup
    user_id = uuid.uuid4()
    current_user = User(
        id=uuid.uuid4(),  # Different ID
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    # Mock repository to return None
    endpoint._Users__user_repo.get_by_id.return_value = None

    # Mock request
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    with patch("app.api.endpoints.users.get_user_id_from_request") as mock_get_user_id:
        mock_get_user_id.return_value = current_user.id

        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await endpoint.delete_user(request, user_id)

        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert excinfo.value.detail == "User not found"
        endpoint._Users__user_repo.get_by_id.assert_awaited_once_with(user_id)
        endpoint._Users__user_repo.delete.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_user_unauthorized(users_endpoint_with_di):
    """Test deleting user when not authorized."""
    endpoint = users_endpoint_with_di

    # Setup
    user_id = uuid.uuid4()
    db_user = User(
        id=user_id,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    current_user = User(
        id=uuid.uuid4(),  # Different ID
        username="otheruser",
        email="other@example.com",
        hashed_password="hashed",
    )

    # Mock repository
    endpoint._Users__user_repo.get_by_id.return_value = db_user

    # Mock request
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"

    with patch("app.api.endpoints.users.get_user_id_from_request") as mock_get_user_id:
        mock_get_user_id.return_value = current_user.id

        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await endpoint.delete_user(request, user_id)

        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == "Not authorized"
        endpoint._Users__user_repo.get_by_id.assert_awaited_once_with(user_id)
        endpoint._Users__user_repo.delete.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_endpoint_has_correct_router_configuration(users_endpoint_with_di):
    """Test that the endpoint has correct router configuration."""
    endpoint = users_endpoint_with_di

    # Verify router configuration
    assert endpoint.ep.prefix == "/users"
    assert "users" in endpoint.ep.tags

    # Verify routes are properly configured
    route_paths = [route.path for route in endpoint.ep.routes]
    assert "/users/me" in route_paths
    assert "/users/{user_id}" in route_paths


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_user_profile_success(users_endpoint_with_di):
    endpoint_cls = users_endpoint_with_di.__class__
    req = Mock(spec=Request)
    req.client = Mock(host="127.0.0.1")

    uid = uuid.uuid4()
    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        from datetime import datetime, timezone

        profile = UserRead(
            id=uid,
            username="alice",
            email="a@example.com",
            hashed_password="x",
            roles=["user"],
            attributes={},
            email_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        async_mock = AsyncMock(return_value=profile)
        endpoint_cls._Users__user_profile_usecase.update_profile = async_mock  # type: ignore[attr-defined]

        payload = UserProfileUpdate(username="alice")
        result = await endpoint_cls.update_user_profile(req, payload)
        assert result == profile
        endpoint_cls._Users__user_profile_usecase.update_profile.assert_awaited_once()  # type: ignore[attr-defined]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_user_profile_validation_error(users_endpoint_with_di):
    endpoint_cls = users_endpoint_with_di.__class__
    req = Mock(spec=Request)
    req.client = Mock(host="127.0.0.1")

    uid = uuid.uuid4()
    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        endpoint_cls._Users__user_profile_usecase.update_profile = AsyncMock(
            side_effect=ProfileUpdateError(  # type: ignore[attr-defined]
                field="username", message="Username already taken"
            )
        )

        with pytest.raises(HTTPException) as exc:
            await endpoint_cls.update_user_profile(
                req, UserProfileUpdate(username="xyz")
            )

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already taken" in exc.value.detail


from app.domain.schemas.user import PasswordChange, UserProfileRead


@pytest.mark.unit
@pytest.mark.asyncio
async def test_change_password_success(users_endpoint_with_di):
    endpoint = users_endpoint_with_di.__class__
    req = Mock(spec=Request)
    req.client = Mock(host="127.0.0.1")

    uid = uuid.uuid4()
    endpoint._Users__user_profile_usecase.change_password = AsyncMock()  # type: ignore[attr-defined]

    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        await endpoint.change_password(
            req,
            PasswordChange(
                current_password="StrongP@ss1", new_password="NewStr0ngP@ss"
            ),
        )
        endpoint._Users__user_profile_usecase.change_password.assert_awaited_once()  # type: ignore[attr-defined]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_change_password_incorrect(users_endpoint_with_di):
    endpoint = users_endpoint_with_di.__class__
    req = Mock(spec=Request)
    uid = uuid.uuid4()
    endpoint._Users__user_profile_usecase.change_password = AsyncMock(side_effect=Exception("Current password is incorrect"))  # type: ignore[attr-defined]

    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        with pytest.raises(HTTPException) as exc:
            await endpoint.change_password(
                req,
                PasswordChange(
                    current_password="StrongP@ss1", new_password="Weakpass1"
                ),
            )
        assert exc.value.status_code == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_notification_preferences_success(users_endpoint_with_di):
    endpoint_cls = users_endpoint_with_di.__class__
    uid = uuid.uuid4()
    from datetime import datetime, timezone

    updated = UserProfileRead(
        id=uid,
        username="x",
        email="y@example.com",
        hashed_password="x",
        email_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    endpoint_cls._Users__user_profile_usecase.update_notification_preferences = AsyncMock(return_value=updated)  # type: ignore[attr-defined]

    req = Mock(spec=Request)
    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        res = await endpoint_cls.update_notification_preferences(req, {"email": False})
        assert res == updated


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_notification_preferences_validation_error(users_endpoint_with_di):
    endpoint_cls = users_endpoint_with_di.__class__
    uid = uuid.uuid4()
    endpoint_cls._Users__user_profile_usecase.update_notification_preferences = AsyncMock(side_effect=ProfileUpdateError(field="email", message="bad"))  # type: ignore[attr-defined]
    req = Mock(spec=Request)

    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        with pytest.raises(HTTPException) as exc:
            await endpoint_cls.update_notification_preferences(req, {"email": True})
        assert exc.value.status_code == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_account_success(users_endpoint_with_di):
    endpoint_cls = users_endpoint_with_di.__class__
    uid = uuid.uuid4()
    endpoint_cls._Users__user_profile_usecase.delete_account = AsyncMock(return_value=True)  # type: ignore[attr-defined]
    req = Mock(spec=Request)
    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        await endpoint_cls.delete_current_user_account(req)  # returns None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_account_not_found(users_endpoint_with_di):
    endpoint_cls = users_endpoint_with_di.__class__
    uid = uuid.uuid4()
    endpoint_cls._Users__user_profile_usecase.delete_account = AsyncMock(return_value=False)  # type: ignore[attr-defined]
    req = Mock(spec=Request)
    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        with pytest.raises(HTTPException) as exc:
            await endpoint_cls.delete_current_user_account(req)
        assert exc.value.status_code == 500


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_picture_success(users_endpoint_with_di):
    endpoint_cls = users_endpoint_with_di.__class__
    uid = uuid.uuid4()
    endpoint_cls._Users__file_upload_service.upload_profile_picture = AsyncMock(return_value="https://img")  # type: ignore[attr-defined]
    endpoint_cls._Users__user_profile_usecase.update_profile = AsyncMock()  # type: ignore[attr-defined]

    fake_file = Mock(filename="pic.png")
    req = Mock(spec=Request)

    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        res = await endpoint_cls.upload_profile_picture(req, fake_file)
        assert res["profile_picture_url"] == "https://img"
        endpoint_cls._Users__file_upload_service.upload_profile_picture.assert_awaited_once()  # type: ignore[attr-defined]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_picture_error(users_endpoint_with_di):
    endpoint_cls = users_endpoint_with_di.__class__
    uid = uuid.uuid4()
    endpoint_cls._Users__file_upload_service.upload_profile_picture = AsyncMock(side_effect=FileUploadError("bad", "E400"))  # type: ignore[attr-defined]
    fake_file = Mock(filename="pic.png")
    req = Mock(spec=Request)

    with patch("app.api.endpoints.users.get_user_id_from_request", return_value=uid):
        with pytest.raises(HTTPException) as exc:
            await endpoint_cls.upload_profile_picture(req, fake_file)
        assert exc.value.status_code == 400
