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
            wallet_address="0xabc",
            timestamp=1000,
            total_value_usd=100.0,
            token_count=2,
            largest_position="ETH",
            largest_position_value_usd=60.0,
        ),
        PortfolioSnapshot(
            wallet_address="0xabc",
            timestamp=2000,
            total_value_usd=200.0,
            token_count=3,
            largest_position="BTC",
            largest_position_value_usd=120.0,
        ),
    ]

    # Mock the repository method to return our test data
    repository = (
        portfolio_snapshot_usecase_with_di._PortfolioSnapshotUsecase__repository
    )
    repository.get_snapshots_in_range = AsyncMock(return_value=mock_data)

    # First call - should call repository
    result1 = await portfolio_snapshot_usecase_with_di.get_timeline("0xabc", 500, 2500)
    assert len(result1) == 2

    # Second call - should hit cache (repository should not be called again)
    result2 = await portfolio_snapshot_usecase_with_di.get_timeline("0xabc", 500, 2500)
    assert len(result2) == 2

    # Verify repository was called only once (first call)
    repository.get_snapshots_in_range.assert_called_once()

    # Results should be identical due to caching
    assert result1 == result2
