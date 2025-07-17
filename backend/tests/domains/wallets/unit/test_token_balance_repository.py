import uuid
from contextlib import asynccontextmanager
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.schemas.token_balance import TokenBalanceCreate
from app.models.token_balance import TokenBalance
from app.repositories.token_balance_repository import TokenBalanceRepository


def setup_mock_session(repository, mock_session):
    """Set up the mock session for the repository."""
    # The mock_database fixture already provides a proper async context manager
    # We need to replace the get_session method with one that returns our mock_session
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    repository._TokenBalanceRepository__database.get_session = mock_get_session


@pytest.mark.asyncio
async def test_token_balance_repository_create(
    token_balance_repository_with_di, mock_async_session
):
    """Test token balance creation with dependency injection."""
    # Setup mock session
    setup_mock_session(token_balance_repository_with_di, mock_async_session)

    # Create test data
    balance_data = TokenBalanceCreate(
        wallet_id=uuid.uuid4(),
        token_id=uuid.uuid4(),
        balance=Decimal("100.50"),
        balance_usd=Decimal("150.75"),
    )

    # Configure mocks
    mock_async_session.add = Mock()
    mock_async_session.commit = AsyncMock()
    mock_async_session.refresh = AsyncMock()

    # Mock the returned balance object
    mock_balance = Mock()
    mock_balance.id = uuid.uuid4()
    mock_async_session.refresh.return_value = mock_balance

    # Execute
    await token_balance_repository_with_di.create(balance_data)

    # Verify
    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()

    # NOTE: Since we're mocking the session, we can't test the actual returned value
    # In a real integration test, we would check balance properties
