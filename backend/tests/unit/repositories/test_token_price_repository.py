import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.schemas.token_price import TokenPriceCreate
from app.models.token_price import TokenPrice
from app.repositories.token_price_repository import TokenPriceRepository


def setup_mock_session(repository, mock_session):
    """Set up the mock session for the repository."""
    # The mock_database fixture already provides a proper async context manager
    # We need to replace the get_session method with one that returns our mock_session
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    repository._TokenPriceRepository__database.get_session = mock_get_session


@pytest.mark.asyncio
async def test_token_price_repository_create(
    token_price_repository_with_di, mock_async_session
):
    """Test token price creation with dependency injection."""
    # Setup mock session
    setup_mock_session(token_price_repository_with_di, mock_async_session)

    # Create test data
    price_data = TokenPriceCreate(
        token_id=uuid.uuid4(),
        price_usd=1.23,
        market_cap_usd=1000000.00,
    )

    # Configure mocks
    mock_async_session.add = Mock()
    mock_async_session.commit = AsyncMock()
    mock_async_session.refresh = AsyncMock()

    # Mock the returned price object
    mock_price = Mock()
    mock_price.id = uuid.uuid4()
    mock_async_session.refresh.return_value = mock_price

    # Execute
    result = await token_price_repository_with_di.create(price_data)

    # Verify
    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once()

    # NOTE: Since we're mocking the session, we can't test the actual returned value
    # In a real integration test, we would check price properties
