import pytest

from app.adapters.protocols.base import ProtocolAdapter
from app.aggregators.protocol_aggregator import (
    aggregate_portfolio_metrics_from_adapters,
)
from app.schemas.defi import (
    Borrowing,
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
    StakedPosition,
)


class _StaticAdapter(ProtocolAdapter):
    """Test adapter returning a fixed snapshot payload."""

    def __init__(self, name: str, snapshot: DeFiAccountSnapshot | None):
        self._name = name
        self._snapshot = snapshot

    # ProtocolAdapter requires .name attribute
    @property  # type: ignore[override]
    def name(self):  # noqa: D401 – simple property
        return self._name

    async def fetch_snapshot(self, address: str):  # noqa: D401 – test impl
        return self._snapshot


@pytest.mark.asyncio
async def test_aggregator_merges_basic_metrics():
    address = "0xABC"

    snap_aave = DeFiAccountSnapshot(
        user_address=address,
        timestamp=0,
        collaterals=[
            Collateral(
                protocol=ProtocolName.aave, asset="DAI", amount=100, usd_value=100
            )
        ],
        borrowings=[
            Borrowing(
                protocol=ProtocolName.aave,
                asset="USDC",
                amount=50,
                usd_value=50,
                interest_rate=0.03,
            )
        ],
        staked_positions=[
            StakedPosition(
                protocol=ProtocolName.aave,
                asset="AAVE",
                amount=10,
                usd_value=1000,
                apy=0.08,
            )
        ],
        health_scores=[HealthScore(protocol=ProtocolName.aave, score=2.0)],
        total_apy=0.08,
    )

    # Compound adapter returns None to exercise missing snapshot branch

    adapters = [
        _StaticAdapter("aave", snap_aave),
        _StaticAdapter("compound", None),
    ]

    metrics = await aggregate_portfolio_metrics_from_adapters(address, adapters)

    assert metrics.total_collateral == pytest.approx(100)
    assert metrics.total_borrowings == pytest.approx(50)
    # Health score aggregated should equal single score 2.0
    assert metrics.aggregate_health_score == pytest.approx(2.0)
    # Protocol breakdown should include both protocols
    assert set(metrics.protocol_breakdown.keys()) == {"aave", "compound"}
    assert metrics.protocol_breakdown["compound"].total_collateral == 0
    assert metrics.protocol_breakdown["aave"].total_collateral == pytest.approx(100)


@pytest.mark.asyncio
async def test_aggregate_multiple_adapters_metrics():
    """Aggregate metrics across collateral-only, borrowing-only and missing snapshots."""
    address = "0xABC"
    now = 0

    snap_collateral = DeFiAccountSnapshot(
        user_address=address,
        timestamp=now,
        collaterals=[
            Collateral(
                protocol=ProtocolName.aave,
                asset="DAI",
                amount=100,
                usd_value=100,
            )
        ],
        borrowings=[],
        staked_positions=[],
        health_scores=[HealthScore(protocol=ProtocolName.aave, score=2.0)],
        total_apy=None,
    )

    snap_borrow = DeFiAccountSnapshot(
        user_address=address,
        timestamp=now,
        collaterals=[],
        borrowings=[
            Borrowing(
                protocol=ProtocolName.compound,
                asset="USDC",
                amount=40,
                usd_value=40,
                interest_rate=0.02,
            )
        ],
        staked_positions=[
            StakedPosition(
                protocol=ProtocolName.compound,
                asset="COMP",
                amount=5,
                usd_value=200,
                apy=0.05,
            )
        ],
        health_scores=[HealthScore(protocol=ProtocolName.compound, score=1.5)],
        total_apy=0.05,
    )

    adapters = [
        _StaticAdapter("aave", snap_collateral),
        _StaticAdapter("compound", snap_borrow),
        _StaticAdapter("radiant", None),
    ]

    metrics = await aggregate_portfolio_metrics_from_adapters(address, adapters)

    assert metrics.total_collateral == pytest.approx(100)
    assert metrics.total_borrowings == pytest.approx(40)
    assert metrics.aggregate_health_score == pytest.approx((2.0 + 1.5) / 2)
    assert metrics.protocol_breakdown["radiant"].total_collateral == 0
