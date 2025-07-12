from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.endpoints import users
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead


@pytest.mark.asyncio
async def test_read_current_user_success():
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

    with patch("app.api.endpoints.users.Audit") as mock_audit:
        # Execute
        result = await users.read_current_user(request, user)

        # Assert
        assert isinstance(result, User)
        assert result.id == user.id
        assert result.username == user.username
        assert result.email == user.email
        mock_audit.info.assert_called_once()


@pytest.mark.asyncio
async def test_read_current_user_inactive():
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

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await users.read_current_user(request, user)

    assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
    assert excinfo.value.detail == "Inactive or disabled user account"


@pytest.mark.asyncio
async def test_update_user_success():
    # Setup
    user_id = uuid.uuid4()
    current_user = User(
        id=user_id,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    db = AsyncMock(spec=AsyncSession)

    # Create mock repository and updated user
    mock_repo = AsyncMock(spec=UserRepository)
    updated_user = User(
        id=user_id,
        username="updated_user",
        email="updated@example.com",
        hashed_password="hashed",
    )
    mock_repo.get_by_id.return_value = current_user
    mock_repo.update.return_value = updated_user

    # Mock UserRepository constructor
    with patch("app.api.endpoints.users.UserRepository", return_value=mock_repo):
        user_in = UserCreate(
            username="updated_user",
            email="updated@example.com",
            password="StrongP@ss123",
        )

        # Execute
        result = await users.update_user(user_id, user_in, db, current_user)

        # Assert
        assert result == updated_user
        mock_repo.get_by_id.assert_awaited_once_with(user_id)
        mock_repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_user_not_found():
    # Setup
    user_id = uuid.uuid4()
    current_user = User(
        id=uuid.uuid4(),  # Different ID
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    db = AsyncMock(spec=AsyncSession)

    # Create mock repository
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_id.return_value = None

    # Mock UserRepository constructor
    with patch("app.api.endpoints.users.UserRepository", return_value=mock_repo):
        user_in = UserCreate(
            username="updated_user",
            email="updated@example.com",
            password="StrongP@ss123",
        )

        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await users.update_user(user_id, user_in, db, current_user)

        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert excinfo.value.detail == "User not found"
        mock_repo.get_by_id.assert_awaited_once_with(user_id)
        mock_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_user_unauthorized():
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

    db = AsyncMock(spec=AsyncSession)

    # Create mock repository
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_id.return_value = db_user

    # Mock UserRepository constructor
    with patch("app.api.endpoints.users.UserRepository", return_value=mock_repo):
        user_in = UserCreate(
            username="updated_user",
            email="updated@example.com",
            password="StrongP@ss123",
        )

        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await users.update_user(user_id, user_in, db, current_user)

        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == "Not authorized"
        mock_repo.get_by_id.assert_awaited_once_with(user_id)
        mock_repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_user_success():
    # Setup
    user_id = uuid.uuid4()
    current_user = User(
        id=user_id,
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    db = AsyncMock(spec=AsyncSession)

    # Create mock repository
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_id.return_value = current_user

    # Mock UserRepository constructor
    with patch("app.api.endpoints.users.UserRepository", return_value=mock_repo):
        # Execute
        result = await users.delete_user(user_id, db, current_user)

        # Assert
        assert result is None
        mock_repo.get_by_id.assert_awaited_once_with(user_id)
        mock_repo.delete.assert_awaited_once_with(current_user)


@pytest.mark.asyncio
async def test_delete_user_not_found():
    # Setup
    user_id = uuid.uuid4()
    current_user = User(
        id=uuid.uuid4(),  # Different ID
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
    )

    db = AsyncMock(spec=AsyncSession)

    # Create mock repository
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_id.return_value = None

    # Mock UserRepository constructor
    with patch("app.api.endpoints.users.UserRepository", return_value=mock_repo):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await users.delete_user(user_id, db, current_user)

        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert excinfo.value.detail == "User not found"
        mock_repo.get_by_id.assert_awaited_once_with(user_id)
        mock_repo.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_user_unauthorized():
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

    db = AsyncMock(spec=AsyncSession)

    # Create mock repository
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_id.return_value = db_user

    # Mock UserRepository constructor
    with patch("app.api.endpoints.users.UserRepository", return_value=mock_repo):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await users.delete_user(user_id, db, current_user)

        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == "Not authorized"
        mock_repo.get_by_id.assert_awaited_once_with(user_id)
        mock_repo.delete.assert_not_awaited()
