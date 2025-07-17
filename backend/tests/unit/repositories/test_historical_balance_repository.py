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
    expected_balance = HistoricalBalance(
        id=uuid.uuid4(),
        wallet_id=balance_data.wallet_id,
        token_id=balance_data.token_id,
        balance=balance_data.balance,
        balance_usd=balance_data.balance_usd,
        timestamp=balance_data.timestamp,
    )
    mock_async_session.refresh = AsyncMock()  # Use AsyncMock for async method

    # Execute the test
    balance = await historical_balance_repository_with_di.create(balance_data)

    # Verify the results
    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()
