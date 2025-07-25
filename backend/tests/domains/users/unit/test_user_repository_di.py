"""
Test UserRepository using new dependency injection pattern.

This demonstrates the new testing approach where repositories receive
their dependencies through constructor injection rather than direct
session instantiation.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.repositories.user_repository import UserRepository


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""
    from contextlib import asynccontextmanager
    from unittest.mock import AsyncMock

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._UserRepository__database.get_session = mock_get_session


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_get_by_id_success(
    user_repository_with_di, mock_database
):
    """Test successful user retrieval by ID with dependency injection."""
    # Arrange
    user_id = uuid.uuid4()
    expected_user = User(id=user_id, username="testuser", email="test@example.com")

    # Mock the database session
    mock_session = AsyncMock()
    mock_session.get.return_value = expected_user
    setup_mock_session(user_repository_with_di, mock_session)

    # Act
    result = await user_repository_with_di.get_by_id(str(user_id))

    # Assert
    assert result == expected_user
    mock_session.get.assert_called_once_with(User, user_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_get_by_id_not_found(
    user_repository_with_di, mock_database
):
    """Test user retrieval by ID when user not found."""
    # Arrange
    user_id = uuid.uuid4()

    # Mock the database session
    mock_session = AsyncMock()
    mock_session.get.return_value = None
    setup_mock_session(user_repository_with_di, mock_session)

    # Act
    result = await user_repository_with_di.get_by_id(str(user_id))

    # Assert
    assert result is None
    mock_session.get.assert_called_once_with(User, user_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_get_by_email_success(
    user_repository_with_di, mock_database
):
    """Test successful user retrieval by email with dependency injection."""
    # Arrange
    email = "test@example.com"
    expected_user = User(id=uuid.uuid4(), username="testuser", email=email)

    # Mock the database session and query result
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=expected_user)
    mock_session.execute = AsyncMock(return_value=mock_result)
    setup_mock_session(user_repository_with_di, mock_session)

    # Act
    result = await user_repository_with_di.get_by_email(email)

    # Assert
    assert result == expected_user
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_save_success(
    user_repository_with_di, mock_database, mock_audit
):
    """Test successful user save with dependency injection."""
    # Arrange
    user = User(username="newuser", email="new@example.com")

    # Mock the database session
    mock_session = AsyncMock()
    setup_mock_session(user_repository_with_di, mock_session)

    # Act
    result = await user_repository_with_di.save(user)

    # Assert
    assert result == user
    mock_session.add.assert_called_once_with(user)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(user)
    mock_audit.info.assert_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_save_integrity_error(
    user_repository_with_di, mock_database, mock_audit
):
    """Test user save with integrity error and proper rollback."""
    # Arrange
    user = User(username="duplicate", email="duplicate@example.com")

    # Mock the database session to raise IntegrityError on commit
    mock_session = AsyncMock()
    mock_session.commit.side_effect = IntegrityError("duplicate", None, None)
    setup_mock_session(user_repository_with_di, mock_session)

    # Act & Assert
    with pytest.raises(IntegrityError):
        await user_repository_with_di.save(user)

    # Verify rollback was called
    mock_session.add.assert_called_once_with(user)
    mock_session.rollback.assert_called_once()
    mock_audit.error.assert_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_exists_true(user_repository_with_di, mock_database):
    """Test user exists check returns True when user exists."""
    # Arrange
    username = "existinguser"

    # Mock the database session and query result
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(
        return_value="some_id"
    )  # Non-None means user exists
    mock_session.execute = AsyncMock(return_value=mock_result)
    setup_mock_session(user_repository_with_di, mock_session)

    # Act
    result = await user_repository_with_di.exists(username=username)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_exists_false(user_repository_with_di, mock_database):
    """Test user exists check returns False when user doesn't exist."""
    # Arrange
    username = "nonexistentuser"

    # Mock the database session and query result
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(
        return_value=None
    )  # None means user doesn't exist
    mock_session.execute = AsyncMock(return_value=mock_result)
    setup_mock_session(user_repository_with_di, mock_session)

    # Act
    result = await user_repository_with_di.exists(username=username)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_audit_logging(
    user_repository_with_di, mock_database, mock_audit
):
    """Test that audit logging is called appropriately."""
    # Arrange
    user_id = uuid.uuid4()

    # Mock the database session
    mock_session = AsyncMock()
    mock_session.get.return_value = None
    setup_mock_session(user_repository_with_di, mock_session)

    # Act
    await user_repository_with_di.get_by_id(str(user_id))

    # Assert audit logging was called
    mock_audit.info.assert_called()


@pytest.mark.unit
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
