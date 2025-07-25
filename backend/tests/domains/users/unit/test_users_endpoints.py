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

from app.domain.schemas.user import UserCreate
from app.models.user import User
from tests.shared.fixtures.enhanced_mocks import MockBehavior
from tests.shared.fixtures.enhanced_mocks.assertions import MockAssertions


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
