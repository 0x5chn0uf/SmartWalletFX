from unittest.mock import patch

import pytest

from app.schemas.defi import (
    Borrowing,
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
    StakedPosition,
)
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioAggregationUsecase,
    PortfolioMetrics,
)


@pytest.mark.asyncio
async def test_portfolio_aggregation_metrics():
    """Verify totals & averages across mocked protocol snapshots."""

    def make_snapshot(mult: float):
        return DeFiAccountSnapshot.model_construct(
            user_address="0xabc",
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
        )

    snapshots = [make_snapshot(1), make_snapshot(2), make_snapshot(3)]

    with patch(
        "app.usecase.defi_aave_usecase.AaveUsecase.get_user_snapshot",
        return_value=snapshots[0],
    ), patch(
        "app.usecase.defi_compound_usecase.CompoundUsecase.get_user_snapshot",
        return_value=snapshots[1],
    ), patch(
        "app.usecase.defi_radiant_usecase.RadiantUsecase.get_user_snapshot",
        return_value=snapshots[2],
    ):
        usecase = PortfolioAggregationUsecase()
        result = await usecase.aggregate_portfolio_metrics("0xabc")

    assert result.total_collateral_usd == pytest.approx(60)
    assert result.total_borrowings_usd == pytest.approx(30)
    assert set(result.protocol_breakdown.keys()) == {
        "aave",
        "compound",
        "radiant",
    }
    assert result.aggregate_health_score == pytest.approx((1 + 2 + 3) / 3)
