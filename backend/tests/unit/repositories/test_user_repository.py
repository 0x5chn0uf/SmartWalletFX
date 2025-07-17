import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace
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


@pytest.fixture
def mock_database():
    """Mock CoreDatabase."""
    return Mock()


@pytest.fixture
def mock_audit():
    """Mock Audit service."""
    return Mock()


@pytest.fixture
def user_repository(mock_database, mock_audit):
    """Create UserRepository with mocked dependencies."""
    return UserRepository(mock_database, mock_audit)


@pytest.mark.asyncio
async def test_user_repository_crud_and_exists(user_repository, db_session):
    """Full happy-path coverage for save, get_* and exists helpers."""
    # Setup mock session
    setup_mock_session(user_repository, db_session)

    # Save a new user
    user = User(
        username=f"alice-{uuid.uuid4().hex[:8]}",
        email=f"alice-{uuid.uuid4().hex[:8]}@example.com",
    )
    saved = await user_repository.save(user)

    assert saved.id is not None

    # Fetch by username / email
    by_username = await user_repository.get_by_username(user.username)
    by_email = await user_repository.get_by_email(user.email)
    assert by_username is saved
    assert by_email is saved

    # exists helper (positive cases)
    assert await user_repository.exists(username=user.username) is True
    assert await user_repository.exists(email=user.email) is True

    # Negative case – non-existing
    assert await user_repository.exists(username="bob-doesnotexist") is False
    assert await user_repository.get_by_username("bob-doesnotexist") is None


@pytest.mark.asyncio
async def test_user_repository_save_integrity_error(user_repository):
    """save should rollback the transaction and propagate IntegrityError."""

    class DummySession:  # noqa: D101 – minimal async session stub
        def __init__(self):
            self.add_called = False
            self.rollback_called = False
            self.refresh_called = False

        # SQLAlchemy's "add" is sync
        def add(self, obj):
            self.add_called = True

        async def commit(self):
            raise IntegrityError("duplicate", None, None)

        async def rollback(self):
            self.rollback_called = True

        async def refresh(self, obj):
            self.refresh_called = True

    # Create a mock user object with required attributes
    mock_user = SimpleNamespace()
    mock_user.id = None  # New user without ID yet
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"

    dummy_session = DummySession()
    setup_mock_session(user_repository, dummy_session)

    with pytest.raises(IntegrityError):
        await user_repository.save(mock_user)  # user object not inspected by repo

    assert dummy_session.add_called is True
    assert dummy_session.rollback_called is True
    # refresh should *not* be called because commit failed
    assert dummy_session.refresh_called is False


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
