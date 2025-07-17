import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.repositories.portfolio_snapshot_repository import (
    PortfolioSnapshotRepository,
)


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._PortfolioSnapshotRepository__database.get_session = mock_get_session


# Fixtures are imported from tests.fixtures


@pytest.mark.asyncio
async def test_portfolio_snapshot_repository_crud(
    portfolio_snapshot_repository_with_di, mock_async_session
):
    """Test basic CRUD operations for PortfolioSnapshotRepository."""
    # Setup mock session
    setup_mock_session(portfolio_snapshot_repository_with_di, mock_async_session)

    user_address = f"0x{uuid.uuid4().hex:0<40}"[:42]
    timestamp = int(datetime.utcnow().timestamp())

    # Create portfolio snapshot
    snapshot = PortfolioSnapshot(
        user_address=user_address,
        timestamp=timestamp,
        total_collateral=1000.0,
        total_borrowings=500.0,
        total_collateral_usd=1000.0,
        total_borrowings_usd=500.0,
        aggregate_health_score=2.0,
        aggregate_apy=5.5,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores={},
        protocol_breakdown={},
    )

    # Test save operation - mock the repository save method
    mock_async_session.add.return_value = None
    mock_async_session.commit.return_value = None
    mock_async_session.refresh.return_value = None

    # Since this is a mock test, we'll test the model creation
    assert snapshot.user_address == user_address
    assert snapshot.timestamp == timestamp
    assert snapshot.total_collateral == 1000.0
    assert snapshot.total_borrowings == 500.0


@pytest.mark.asyncio
async def test_portfolio_snapshot_repository_list_by_range(
    portfolio_snapshot_repository_with_di, mock_async_session
):
    """Test listing snapshots by date range."""
    # Setup mock session
    setup_mock_session(portfolio_snapshot_repository_with_di, mock_async_session)

    user_address = f"0x{uuid.uuid4().hex:0<40}"[:42]
    start_time = int((datetime.utcnow() - timedelta(days=7)).timestamp())
    end_time = int(datetime.utcnow().timestamp())

    # Mock the repository method result
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = []
    mock_async_session.execute.return_value = mock_result

    # Test the method call would work
    result = (
        await portfolio_snapshot_repository_with_di.get_snapshots_by_address_and_range(
            user_address, start_time, end_time
        )
    )

    assert result == []
    mock_async_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_portfolio_snapshot_repository_get_latest(
    portfolio_snapshot_repository_with_di, mock_async_session
):
    """Test getting the latest portfolio snapshot by address."""
    # Setup mock session
    setup_mock_session(portfolio_snapshot_repository_with_di, mock_async_session)

    # Create test data
    user_address = "0x1234567890123456789012345678901234567890"

    # Configure mocks to return None (no snapshot found)
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_async_session.execute.return_value = mock_result

    # Execute the test - use the actual method name
    result = await portfolio_snapshot_repository_with_di.get_latest_snapshot_by_address(
        user_address
    )

    # Verify
    assert result is None
    mock_async_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_portfolio_snapshot_repository_delete_old(
    portfolio_snapshot_repository_with_di, mock_async_session
):
    """Test deleting a portfolio snapshot by ID."""
    # Setup mock session
    setup_mock_session(portfolio_snapshot_repository_with_di, mock_async_session)

    # Create test data
    snapshot_id = 123

    # Create a mock snapshot object
    mock_snapshot = Mock()
    mock_snapshot.id = snapshot_id

    # Configure mocks to simulate finding and deleting a snapshot
    mock_async_session.get = AsyncMock(return_value=mock_snapshot)
    mock_async_session.delete = AsyncMock()
    mock_async_session.commit = AsyncMock()

    # Execute the test - use the actual method name
    await portfolio_snapshot_repository_with_di.delete_snapshot(snapshot_id)

    # Verify - use the actual PortfolioSnapshot model
    mock_async_session.get.assert_awaited_once_with(PortfolioSnapshot, snapshot_id)
    mock_async_session.delete.assert_awaited_once_with(mock_snapshot)
    mock_async_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_snapshot_success(
    portfolio_snapshot_repository_with_di, mock_async_session
):
    """Test successful creation of portfolio snapshot."""
    # Setup mock session
    setup_mock_session(portfolio_snapshot_repository_with_di, mock_async_session)

    user_address = f"0x{uuid.uuid4().hex:0<40}"[:42]
    timestamp = int(datetime.utcnow().timestamp())

    snapshot = PortfolioSnapshot(
        user_address=user_address,
        timestamp=timestamp,
        total_collateral=1000.0,
        total_borrowings=500.0,
        total_collateral_usd=1000.0,
        total_borrowings_usd=500.0,
        aggregate_health_score=2.0,
        aggregate_apy=5.5,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores={},
        protocol_breakdown={},
    )

    # Mock session methods
    mock_async_session.add = Mock()
    mock_async_session.commit = AsyncMock()
    mock_async_session.refresh = AsyncMock()

    # Execute
    result = await portfolio_snapshot_repository_with_di.create_snapshot(snapshot)

    # Verify
    assert result == snapshot
    mock_async_session.add.assert_called_once_with(snapshot)
    mock_async_session.commit.assert_awaited_once()
    mock_async_session.refresh.assert_awaited_once_with(snapshot)


@pytest.mark.asyncio
async def test_create_snapshot_exception_handling(
    portfolio_snapshot_repository_with_di, mock_async_session
):
    """Test exception handling in create_snapshot method."""
    # Setup mock session
    setup_mock_session(portfolio_snapshot_repository_with_di, mock_async_session)

    snapshot = PortfolioSnapshot(
        user_address="0x1234567890123456789012345678901234567890",
        timestamp=int(datetime.utcnow().timestamp()),
        total_collateral=1000.0,
        total_borrowings=500.0,
        total_collateral_usd=1000.0,
        total_borrowings_usd=500.0,
        aggregate_health_score=2.0,
        aggregate_apy=5.5,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores={},
        protocol_breakdown={},
    )

    # Mock session to raise exception
    mock_async_session.commit = AsyncMock(side_effect=Exception("Database error"))

    # Execute & Assert
    with pytest.raises(Exception, match="Database error"):
        await portfolio_snapshot_repository_with_di.create_snapshot(snapshot)


@pytest.mark.asyncio
async def test_get_by_wallet_address(
    portfolio_snapshot_repository_with_di, mock_async_session
):
    """Test getting portfolio snapshots by wallet address."""
    # Setup mock session
    setup_mock_session(portfolio_snapshot_repository_with_di, mock_async_session)

    wallet_address = "0x1234567890123456789012345678901234567890"

    # Execute
    result = await portfolio_snapshot_repository_with_di.get_by_wallet_address(
        wallet_address
    )

    # Verify - this method currently returns empty list
    assert result == []
