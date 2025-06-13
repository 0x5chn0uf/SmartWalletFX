from unittest.mock import patch

import pytest

from app.schemas.defi import (
    Borrowing,
    Collateral,
    HealthScore,
    ProtocolName,
    StakedPosition,
)
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioMetrics,
    aggregate_portfolio_metrics,
)


@pytest.mark.asyncio
async def test_portfolio_aggregation_metrics():
    """Verify totals & averages across mocked protocol snapshots."""

    def make_snapshot(mult: float):
        return PortfolioMetrics.model_construct(
            user_address="0xabc",
            total_collateral=10 * mult,
            total_borrowings=5 * mult,
            total_collateral_usd=10 * mult,
            total_borrowings_usd=5 * mult,
            aggregate_health_score=mult,
            aggregate_apy=0.1 * mult,
            collaterals=[
                Collateral(
                    protocol=ProtocolName.aave,
                    asset="USDC",
                    amount=10 * mult,
                    usd_value=10 * mult,
                )
            ],
            borrowings=[
                Borrowing(
                    protocol=ProtocolName.aave,
                    asset="USDC",
                    amount=5 * mult,
                    usd_value=5 * mult,
                    interest_rate=0.03,
                )
            ],
            staked_positions=[
                StakedPosition(
                    protocol=ProtocolName.aave,
                    asset="stkUSDC",
                    amount=1 * mult,
                    usd_value=1 * mult,
                    apy=0.1 * mult,
                )
            ],
            health_scores=[
                HealthScore(protocol=ProtocolName.aave, score=mult)
            ],
            protocol_breakdown={},
            historical_snapshots=None,
            timestamp=0,
        )

    snapshots = [make_snapshot(1), make_snapshot(2), make_snapshot(3)]

    with patch(
        "app.usecase.portfolio_aggregation_usecase.get_aave_user_snapshot_usecase",  # noqa: E501
        return_value=snapshots[0],
    ), patch(
        "app.usecase.portfolio_aggregation_usecase.get_compound_user_snapshot_usecase",  # noqa: E501
        return_value=snapshots[1],
    ), patch(
        "app.usecase.portfolio_aggregation_usecase.get_radiant_user_snapshot_usecase",  # noqa: E501
        return_value=snapshots[2],
    ):
        result = await aggregate_portfolio_metrics("0xabc")

    assert result.total_collateral == pytest.approx(60)
    assert result.total_borrowings == pytest.approx(30)
    assert set(result.protocol_breakdown.keys()) == {
        "aave",
        "compound",
        "radiant",
    }
    assert result.aggregate_health_score == pytest.approx((1 + 2 + 3) / 3)
