from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.repositories.user_repository import UserRepository


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._UserRepository__database.get_session = mock_get_session


# Using shared fixtures from tests.shared.fixtures.core for mock_database and mock_audit


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.merge = AsyncMock()
    session.delete = AsyncMock()
    session.get = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def user_repository(mock_database, mock_audit):
    """Create UserRepository with mocked dependencies."""
    return UserRepository(mock_database, mock_audit)


@pytest.mark.asyncio
async def test_get_all_success(user_repository, mock_session):
    """Test successful retrieval of all users."""
    # Arrange
    setup_mock_session(user_repository, mock_session)

    mock_user1 = Mock()
    mock_user1.id = uuid.uuid4()
    mock_user1.username = "user1"
    mock_user2 = Mock()
    mock_user2.id = uuid.uuid4()
    mock_user2.username = "user2"

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = [mock_user1, mock_user2]
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    result = await user_repository.get_all()

    # Assert
    assert result == [mock_user1, mock_user2]
    mock_session.execute.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_all_exception_handling(user_repository, mock_session):
    """Test exception handling in get_all method."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await user_repository.get_all()

    user_repository._UserRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_username_found(user_repository, mock_session):
    """Test getting user by username when user exists."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    username = "testuser"

    mock_user = Mock()
    mock_user.username = username
    mock_user.id = uuid.uuid4()

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    # Act
    result = await user_repository.get_by_username(username)

    # Assert
    assert result == mock_user
    mock_session.execute.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_username_not_found(user_repository, mock_session):
    """Test getting user by username when user doesn't exist."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    username = "nonexistent"

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await user_repository.get_by_username(username)

    # Assert
    assert result is None
    mock_session.execute.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_username_exception_handling(user_repository, mock_session):
    """Test exception handling in get_by_username method."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await user_repository.get_by_username("testuser")

    user_repository._UserRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_email_found(user_repository, mock_session):
    """Test getting user by email when user exists."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    email = "test@example.com"

    mock_user = Mock()
    mock_user.email = email
    mock_user.id = uuid.uuid4()

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    # Act
    result = await user_repository.get_by_email(email)

    # Assert
    assert result == mock_user
    mock_session.execute.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_email_not_found(user_repository, mock_session):
    """Test getting user by email when user doesn't exist."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    email = "nonexistent@example.com"

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await user_repository.get_by_email(email)

    # Assert
    assert result is None
    mock_session.execute.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_email_exception_handling(user_repository, mock_session):
    """Test exception handling in get_by_email method."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await user_repository.get_by_email("test@example.com")

    user_repository._UserRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_exists_by_username_true(user_repository, mock_session):
    """Test exists check returns True when user exists by username."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    username = "existinguser"

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = "some_id"
    mock_session.execute.return_value = mock_result

    # Act
    result = await user_repository.exists(username=username)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_exists_by_email_true(user_repository, mock_session):
    """Test exists check returns True when user exists by email."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    email = "existing@example.com"

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = "some_id"
    mock_session.execute.return_value = mock_result

    # Act
    result = await user_repository.exists(email=email)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_exists_by_both_username_and_email(user_repository, mock_session):
    """Test exists check with both username and email."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    username = "testuser"
    email = "test@example.com"

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = "some_id"
    mock_session.execute.return_value = mock_result

    # Act
    result = await user_repository.exists(username=username, email=email)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_exists_false(user_repository, mock_session):
    """Test exists check returns False when user doesn't exist."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    username = "nonexistent"

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await user_repository.exists(username=username)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_exists_exception_handling(user_repository, mock_session):
    """Test exception handling in exists method."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await user_repository.exists(username="testuser")

    user_repository._UserRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id_with_uuid(user_repository, mock_session):
    """Test getting user by ID when passed as UUID."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    user_id = uuid.uuid4()

    mock_user = Mock()
    mock_user.id = user_id
    mock_session.get.return_value = mock_user

    # Act
    result = await user_repository.get_by_id(user_id)

    # Assert
    assert result == mock_user
    mock_session.get.assert_called_once_with(User, user_id)
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_id_with_string(user_repository, mock_session):
    """Test getting user by ID when passed as string."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    user_id = uuid.uuid4()
    user_id_str = str(user_id)

    mock_user = Mock()
    mock_user.id = user_id
    mock_session.get.return_value = mock_user

    # Act
    result = await user_repository.get_by_id(user_id_str)

    # Assert
    assert result == mock_user
    mock_session.get.assert_called_once_with(User, user_id)
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_id_invalid_uuid_string(user_repository, mock_session):
    """Test getting user by ID with invalid UUID string."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    invalid_id = "invalid-uuid"

    mock_user = Mock()
    mock_session.get.return_value = mock_user

    # Act
    result = await user_repository.get_by_id(invalid_id)

    # Assert
    assert result == mock_user
    mock_session.get.assert_called_once_with(User, invalid_id)
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_id_exception_handling(user_repository, mock_session):
    """Test exception handling in get_by_id method."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.get.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await user_repository.get_by_id(uuid.uuid4())

    user_repository._UserRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_save_success(user_repository, mock_session):
    """Test successful save of user."""
    # Arrange
    setup_mock_session(user_repository, mock_session)

    user = User(username="testuser", email="test@example.com")

    # Act
    result = await user_repository.save(user)

    # Assert
    assert result == user
    mock_session.add.assert_called_once_with(user)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(user)
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_save_integrity_error(user_repository, mock_session):
    """Test save with integrity error handling."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.commit.side_effect = IntegrityError("duplicate", None, None)

    user = User(username="testuser", email="test@example.com")

    # Act & Assert
    with pytest.raises(IntegrityError):
        await user_repository.save(user)

    mock_session.rollback.assert_called_once()
    user_repository._UserRepository__audit.error.assert_called()


@pytest.mark.asyncio
async def test_save_general_exception_handling(user_repository, mock_session):
    """Test general exception handling in save method."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.add.side_effect = Exception("Database error")

    user = User(username="testuser", email="test@example.com")

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await user_repository.save(user)

    user_repository._UserRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_update_success(user_repository, mock_session):
    """Test successful update of user."""
    # Arrange
    setup_mock_session(user_repository, mock_session)

    user = User(username="testuser", email="test@example.com")
    user.id = uuid.uuid4()

    mock_merged_user = Mock()
    mock_merged_user.id = user.id
    mock_merged_user.email_verified = False
    mock_session.merge.return_value = mock_merged_user

    # Act
    result = await user_repository.update(user, email_verified=True)

    # Assert
    assert result == mock_merged_user
    assert mock_merged_user.email_verified is True
    mock_session.merge.assert_called_once_with(user)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_merged_user)
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_update_with_invalid_field(user_repository, mock_session):
    """Test update ignores invalid fields."""
    # Arrange
    setup_mock_session(user_repository, mock_session)

    user = User(username="testuser", email="test@example.com")
    user.id = uuid.uuid4()

    mock_merged_user = Mock(
        spec=[
            "id",
            "username",
            "email",
            "hashed_password",
            "email_verified",
            "roles",
            "attributes",
            "created_at",
            "updated_at",
        ]
    )
    mock_merged_user.id = user.id
    mock_session.merge.return_value = mock_merged_user

    # Act
    result = await user_repository.update(
        user, invalid_field="value", email_verified=True
    )

    # Assert
    assert result == mock_merged_user
    # Invalid field should be ignored
    assert not hasattr(mock_merged_user, "invalid_field")
    mock_session.merge.assert_called_once_with(user)
    mock_session.commit.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_update_integrity_error(user_repository, mock_session):
    """Test update with integrity error handling."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.commit.side_effect = IntegrityError("duplicate", None, None)

    user = User(username="testuser", email="test@example.com")
    user.id = uuid.uuid4()

    mock_merged_user = Mock()
    mock_merged_user.id = user.id
    mock_session.merge.return_value = mock_merged_user

    # Act & Assert
    with pytest.raises(IntegrityError):
        await user_repository.update(user, email_verified=True)

    mock_session.rollback.assert_called_once()
    user_repository._UserRepository__audit.error.assert_called()


@pytest.mark.asyncio
async def test_update_general_exception_handling(user_repository, mock_session):
    """Test general exception handling in update method."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.merge.side_effect = Exception("Database error")

    user = User(username="testuser", email="test@example.com")
    user.id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await user_repository.update(user, email_verified=True)

    user_repository._UserRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_delete_success(user_repository, mock_session):
    """Test successful deletion of user."""
    # Arrange
    setup_mock_session(user_repository, mock_session)

    user = User(username="testuser", email="test@example.com")
    user.id = uuid.uuid4()

    mock_merged_user = Mock()
    mock_merged_user.id = user.id
    mock_session.merge.return_value = mock_merged_user

    # Act
    result = await user_repository.delete(user)

    # Assert
    assert result is None
    mock_session.execute.assert_called_once()  # Delete refresh tokens
    mock_session.merge.assert_called_once_with(user)
    mock_session.delete.assert_called_once_with(mock_merged_user)
    mock_session.commit.assert_called_once()
    user_repository._UserRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_delete_exception_handling(user_repository, mock_session):
    """Test exception handling in delete method."""
    # Arrange
    setup_mock_session(user_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    user = User(username="testuser", email="test@example.com")
    user.id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await user_repository.delete(user)

    user_repository._UserRepository__audit.error.assert_called_once()


def test_user_repository_constructor_dependencies():
    """Test that UserRepository properly accepts dependencies in constructor."""
    # Arrange
    mock_database = Mock()
    mock_audit = Mock()

    # Act
    repository = UserRepository(mock_database, mock_audit)

    # Assert
    assert repository._UserRepository__database == mock_database
    assert repository._UserRepository__audit == mock_audit
