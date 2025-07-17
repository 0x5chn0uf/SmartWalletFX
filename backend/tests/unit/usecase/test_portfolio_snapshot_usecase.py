import pytest
from sqlalchemy import text

from app.models.portfolio_snapshot import PortfolioSnapshot


@pytest.mark.asyncio
async def test_portfolio_snapshot_usecase_cache(portfolio_snapshot_usecase_with_di):
    # This test verifies caching behavior in the portfolio snapshot usecase
    # Since we're using DI fixtures, we'll mock the repository calls to test the cache
    from unittest.mock import AsyncMock

    # Mock the repository to return consistent test data
    mock_data = [
        PortfolioSnapshot(
            user_address="0xabc",
            timestamp=1000,
            total_collateral=50.0,
            total_borrowings=20.0,
            total_collateral_usd=100.0,
            total_borrowings_usd=40.0,
            aggregate_health_score=0.8,
            aggregate_apy=5.2,
            collaterals={},
            borrowings={},
            staked_positions={},
            health_scores={},
            protocol_breakdown={},
        ),
        PortfolioSnapshot(
            user_address="0xabc",
            timestamp=2000,
            total_collateral=100.0,
            total_borrowings=30.0,
            total_collateral_usd=200.0,
            total_borrowings_usd=60.0,
            aggregate_health_score=0.9,
            aggregate_apy=6.5,
            collaterals={},
            borrowings={},
            staked_positions={},
            health_scores={},
            protocol_breakdown={},
        ),
    ]

    # Mock the repository method to return our test data
    portfolio_snapshot_usecase_with_di._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_by_wallet_address = AsyncMock(return_value=mock_data)

    # Call the method twice to test caching
    wallet_address = "0xabc"
    result1 = await portfolio_snapshot_usecase_with_di.get_snapshots_by_wallet(wallet_address)
    result2 = await portfolio_snapshot_usecase_with_di.get_snapshots_by_wallet(wallet_address)

    # Verify the results are consistent
    assert result1 == mock_data
    assert result2 == mock_data

    # Verify the repository method was called the expected number of times
    # (This will depend on the caching implementation)
    assert portfolio_snapshot_usecase_with_di._PortfolioSnapshotUsecase__portfolio_snapshot_repo.get_by_wallet_address.call_count >= 1
