from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.oauth_account import OAuthAccount
from app.repositories.oauth_account_repository import OAuthAccountRepository


@pytest.mark.asyncio
async def test_get_by_provider_account_found():
    # Setup
    session = AsyncMock(spec=AsyncSession)
    repo = OAuthAccountRepository(session)

    # Mock the execute method to return a result with a scalar_one_or_none method
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = OAuthAccount(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        provider="google",
        provider_account_id="123",
        email="test@example.com",
    )
    session.execute.return_value = mock_result

    # Execute
    result = await repo.get_by_provider_account("google", "123")

    # Assert
    assert result is not None
    assert result.provider == "google"
    assert result.provider_account_id == "123"
    session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_provider_account_not_found():
    # Setup
    session = AsyncMock(spec=AsyncSession)
    repo = OAuthAccountRepository(session)

    # Mock the execute method to return a result with a scalar_one_or_none method
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    # Execute
    result = await repo.get_by_provider_account("google", "123")

    # Assert
    assert result is None
    session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_user_provider_found():
    # Setup
    session = AsyncMock(spec=AsyncSession)
    repo = OAuthAccountRepository(session)
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
    session.execute.return_value = mock_result

    # Execute
    result = await repo.get_by_user_provider(user_id, "google")

    # Assert
    assert result is not None
    assert result.user_id == user_id
    assert result.provider == "google"
    session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_user_provider_not_found():
    # Setup
    session = AsyncMock(spec=AsyncSession)
    repo = OAuthAccountRepository(session)
    user_id = uuid.uuid4()

    # Mock the execute method to return a result with a scalar_one_or_none method
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    # Execute
    result = await repo.get_by_user_provider(user_id, "google")

    # Assert
    assert result is None
    session.execute.assert_awaited_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_link_account_with_email():
    # Setup
    session = AsyncMock(spec=AsyncSession)
    repo = OAuthAccountRepository(session)
    user_id = uuid.uuid4()

    # Execute
    result = await repo.link_account(user_id, "google", "123", "test@example.com")

    # Assert
    assert result is not None
    assert result.user_id == user_id
    assert result.provider == "google"
    assert result.provider_account_id == "123"
    assert result.email == "test@example.com"

    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_link_account_without_email():
    # Setup
    session = AsyncMock(spec=AsyncSession)
    repo = OAuthAccountRepository(session)
    user_id = uuid.uuid4()

    # Execute
    result = await repo.link_account(user_id, "github", "456")

    # Assert
    assert result is not None
    assert result.user_id == user_id
    assert result.provider == "github"
    assert result.provider_account_id == "456"
    assert result.email is None

    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_link_account_with_session_exception():
    # Setup
    session = AsyncMock(spec=AsyncSession)
    repo = OAuthAccountRepository(session)
    user_id = uuid.uuid4()

    # Configure the mock to raise an exception on commit
    session.commit.side_effect = Exception("Database error")

    # Execute and Assert
    with pytest.raises(Exception, match="Database error"):
        await repo.link_account(user_id, "google", "123", "test@example.com")

    # Verify that add was called but commit failed
    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_not_awaited()
