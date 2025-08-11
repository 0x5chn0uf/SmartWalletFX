from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.oauth_account import OAuthAccount
from app.repositories.oauth_account_repository import OAuthAccountRepository


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._OAuthAccountRepository__database.get_session = mock_get_session


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_provider_account_found(
    oauth_account_repository_with_di, mock_async_session
):
    """Test finding OAuth account by provider and account ID."""
    # Setup mock session
    setup_mock_session(oauth_account_repository_with_di, mock_async_session)

    # Mock the execute method to return a result with a scalar_one_or_none method
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = OAuthAccount(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        provider="google",
        provider_account_id="123",
        email="test@example.com",
    )
    mock_async_session.execute.return_value = mock_result

    # Execute
    result = await oauth_account_repository_with_di.get_by_provider_account(
        "google", "123"
    )

    # Assert
    assert result is not None
    assert result.provider == "google"
    assert result.provider_account_id == "123"
    mock_async_session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_provider_account_not_found(
    oauth_account_repository_with_di, mock_async_session
):
    """Test not finding OAuth account by provider and account ID."""
    # Setup mock session
    setup_mock_session(oauth_account_repository_with_di, mock_async_session)

    # Mock the execute method to return a result with a scalar_one_or_none method
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_async_session.execute.return_value = mock_result

    # Execute
    result = await oauth_account_repository_with_di.get_by_provider_account(
        "google", "123"
    )

    # Assert
    assert result is None
    mock_async_session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_user_provider_found(
    oauth_account_repository_with_di, mock_async_session
):
    """Test finding OAuth account by user ID and provider."""
    # Setup mock session
    setup_mock_session(oauth_account_repository_with_di, mock_async_session)
    user_id = uuid.uuid4()

    # Mock the execute method to return a result with a scalar_one_or_none method
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = OAuthAccount(
        id=uuid.uuid4(),
        user_id=user_id,
        provider="google",
        provider_account_id="123",
        email="test@example.com",
    )
    mock_async_session.execute.return_value = mock_result

    # Execute
    result = await oauth_account_repository_with_di.get_by_user_provider(
        user_id, "google"
    )

    # Assert
    assert result is not None
    assert result.user_id == user_id
    assert result.provider == "google"
    mock_async_session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_user_provider_not_found(
    oauth_account_repository_with_di, mock_async_session
):
    """Test not finding OAuth account by user ID and provider."""
    # Setup mock session
    setup_mock_session(oauth_account_repository_with_di, mock_async_session)
    user_id = uuid.uuid4()

    # Mock the execute method to return a result with a scalar_one_or_none method
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_async_session.execute.return_value = mock_result

    # Execute
    result = await oauth_account_repository_with_di.get_by_user_provider(
        user_id, "google"
    )

    # Assert
    assert result is None
    mock_async_session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_link_account_with_email(
    oauth_account_repository_with_di, mock_async_session
):
    """Test linking OAuth account with email."""
    # Setup mock session
    setup_mock_session(oauth_account_repository_with_di, mock_async_session)
    user_id = uuid.uuid4()

    # Execute
    result = await oauth_account_repository_with_di.link_account(
        user_id, "google", "123", "test@example.com"
    )

    # Assert
    assert result is not None
    assert result.user_id == user_id
    assert result.provider == "google"
    assert result.provider_account_id == "123"
    assert result.email == "test@example.com"
    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_link_account_without_email(
    oauth_account_repository_with_di, mock_async_session
):
    """Test linking OAuth account without email."""
    # Setup mock session
    setup_mock_session(oauth_account_repository_with_di, mock_async_session)
    user_id = uuid.uuid4()

    # Execute
    result = await oauth_account_repository_with_di.link_account(
        user_id, "github", "456"
    )

    # Assert
    assert result is not None
    assert result.user_id == user_id
    assert result.provider == "github"
    assert result.provider_account_id == "456"
    assert result.email is None
    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_link_account_with_session_exception(
    oauth_account_repository_with_di, mock_async_session
):
    """Test linking OAuth account with database error."""
    # Setup mock session
    setup_mock_session(oauth_account_repository_with_di, mock_async_session)
    user_id = uuid.uuid4()

    # Configure the mock to raise an exception on commit
    mock_async_session.commit.side_effect = Exception("Database error")

    # Execute and Assert
    with pytest.raises(Exception, match="Database error"):
        await oauth_account_repository_with_di.link_account(
            user_id, "google", "123", "test@example.com"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_provider_account_exception(
    oauth_account_repository_with_di, mock_async_session
):
    """Test get_by_provider_account with database exception."""
    # Setup mock session
    setup_mock_session(oauth_account_repository_with_di, mock_async_session)

    # Mock the execute method to raise an exception
    mock_async_session.execute.side_effect = Exception("Database error")

    # Execute and Assert
    with pytest.raises(Exception, match="Database error"):
        await oauth_account_repository_with_di.get_by_provider_account("google", "123")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_user_provider_exception(
    oauth_account_repository_with_di, mock_async_session
):
    """Test get_by_user_provider with database exception."""
    # Setup mock session
    setup_mock_session(oauth_account_repository_with_di, mock_async_session)
    user_id = uuid.uuid4()

    # Mock the execute method to raise an exception
    mock_async_session.execute.side_effect = Exception("Database error")

    # Execute and Assert
    with pytest.raises(Exception, match="Database error"):
        await oauth_account_repository_with_di.get_by_user_provider(user_id, "google")
