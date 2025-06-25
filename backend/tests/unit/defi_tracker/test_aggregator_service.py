from __future__ import annotations

import pytest

from app.domain.defi_tracker.models import Position
from app.domain.defi_tracker.repositories import AggregateMetricsRepository
from app.domain.defi_tracker.services import AggregatorService, ProtocolAdapter


class InMemoryRepo(AggregateMetricsRepository):
    """Simple in-memory repository for unit testing the aggregator."""

    def __init__(self):
        self._store: dict[str, list] = {}

    async def upsert(self, metrics):  # type: ignore[override]
        self._store.setdefault(metrics.wallet_id, []).append(metrics)

    async def get_latest(self, wallet_id: str):  # type: ignore[override]
        return self._store.get(wallet_id, [None])[-1]

    async def get_history(
        self, wallet_id: str, limit: int = 100, offset: int = 0
    ):  # type: ignore[override]
        history = self._store.get(wallet_id, [])
        return history[offset : offset + limit]


class StubAdapter(ProtocolAdapter):
    def __init__(self, positions):
        self._positions = positions
        self.name = "stub"

    async def fetch_positions(self, wallet_id: str):  # type: ignore[override]
        return list(self._positions)


@pytest.mark.asyncio
async def test_aggregate_metrics_computation():
    wallet = "0xabc"
    # Adapter 1 supplies + borrow
    adapter1 = StubAdapter(
        [
            Position(
                protocol="aave", asset="DAI", amount=100, usd_value=100.0, apy=0.05
            ),
            Position(
                protocol="aave", asset="ETH", amount=-1, usd_value=-2000.0, apy=None
            ),
        ]
    )
    # Adapter 2 supplies only
    adapter2 = StubAdapter(
        [
            Position(
                protocol="compound", asset="USDC", amount=50, usd_value=50.0, apy=0.02
            )
        ]
    )

    repo = InMemoryRepo()
    service = AggregatorService([adapter1, adapter2], repo)

    metrics = await service.aggregate(wallet)

    assert metrics.wallet_id == wallet
    assert metrics.tvl == 150.0  # 100 + 50
    assert metrics.total_borrowings == 2000.0  # abs of -2000
    # Weighted APY = (100*0.05 + 50*0.02)/150 = 0.04
    assert round(metrics.aggregate_apy, 4) == 0.04
    # Persisted?
    latest = await repo.get_latest(wallet)
    assert latest == metrics
