import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.user_repository import UserRepository


def setup_mock_session(user_repository_with_di, mock_async_session):
    """Helper to set up mock session for tests."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_session():
        yield mock_async_session

    user_repository_with_di._UserRepository__database.get_session = mock_get_session


@pytest.mark.asyncio
async def test_user_repository_update(user_repository_with_di, mock_async_session):
    """Test user update with dependency injection."""
    # Setup mock session
    setup_mock_session(user_repository_with_di, mock_async_session)

    # Create a user object to update
    user_id = uuid.uuid4()
    mock_user = Mock()
    mock_user.id = user_id
    mock_user.email_verified = False

    # Mock the user retrieval - make merge an AsyncMock since it's awaited
    mock_async_session.merge = AsyncMock(return_value=mock_user)
    mock_async_session.commit = AsyncMock()
    mock_async_session.refresh = AsyncMock()

    # Update the mock user's attributes to reflect the update
    mock_user.email_verified = True

    # Execute the test - pass user object and kwargs
    updated = await user_repository_with_di.update(mock_user, email_verified=True)

    # Verify the result
    assert updated is not None
    assert updated.email_verified is True

    # Verify database operations
    mock_async_session.merge.assert_awaited_once_with(mock_user)
    mock_async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_repository_delete_cascades_refresh_tokens(
    user_repository_with_di, mock_async_session
):
    """Test that deleting a user cascades to refresh tokens."""
    # Setup mock session
    setup_mock_session(user_repository_with_di, mock_async_session)

    # Create test data
    user_id = uuid.uuid4()

    # Create a mock user object
    mock_user = Mock()
    mock_user.id = user_id

    # Configure mocks for delete operations
    mock_async_session.execute = AsyncMock()
    mock_async_session.merge = AsyncMock(return_value=mock_user)
    mock_async_session.delete = AsyncMock()
    mock_async_session.commit = AsyncMock()

    # Execute the test - pass user object instead of UUID
    result = await user_repository_with_di.delete(mock_user)

    # Verify the result (delete method returns None)
    assert result is None

    # Verify database operations
    mock_async_session.execute.assert_awaited_once()  # Delete refresh tokens
    mock_async_session.merge.assert_awaited_once_with(mock_user)
    mock_async_session.delete.assert_awaited_once_with(mock_user)
    mock_async_session.commit.assert_awaited_once()
