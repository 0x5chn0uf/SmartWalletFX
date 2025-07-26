import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.schemas.historical_balance import HistoricalBalanceCreate
from app.models.historical_balance import HistoricalBalance
from app.repositories.historical_balance_repository import (
    HistoricalBalanceRepository,
)


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._HistoricalBalanceRepository__database.get_session = mock_get_session


@pytest.mark.unit
@pytest.mark.asyncio
async def test_historical_balance_repository_create(
    historical_balance_repository_with_di, mock_async_session
):
    """Test historical balance creation with dependency injection."""
    # Setup mock session
    setup_mock_session(historical_balance_repository_with_di, mock_async_session)

    # Create test data
    wallet_id = uuid.uuid4()
    token_id = uuid.uuid4()
    balance_data = HistoricalBalanceCreate(
        wallet_id=wallet_id,
        token_id=token_id,
        balance=100.50,
        balance_usd=105.25,
        timestamp=datetime.now(),
    )

    # Mock the returned balance
    HistoricalBalance(
        id=uuid.uuid4(),
        wallet_id=balance_data.wallet_id,
        token_id=balance_data.token_id,
        balance=balance_data.balance,
        balance_usd=balance_data.balance_usd,
        timestamp=balance_data.timestamp,
    )
    mock_async_session.refresh = AsyncMock()  # Use AsyncMock for async method

    # Execute the test
    await historical_balance_repository_with_di.create(balance_data)

    # Verify the results
    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_historical_balance_repository_create_exception(
    historical_balance_repository_with_di, mock_async_session
):
    """Test historical balance creation with exception handling."""
    # Setup mock session
    setup_mock_session(historical_balance_repository_with_di, mock_async_session)

    # Create test data
    wallet_id = uuid.uuid4()
    token_id = uuid.uuid4()
    balance_data = HistoricalBalanceCreate(
        wallet_id=wallet_id,
        token_id=token_id,
        balance=100.50,
        balance_usd=105.25,
        timestamp=datetime.now(),
    )

    # Mock session to raise exception during commit
    mock_async_session.commit = AsyncMock(side_effect=Exception("Database error"))

    # Execute the test and verify exception is raised
    with pytest.raises(Exception, match="Database error"):
        await historical_balance_repository_with_di.create(balance_data)

    # Verify the operations that should have been called
    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
