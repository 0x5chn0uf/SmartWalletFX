import pytest
from sqlalchemy.orm import Session

from app.adapters.protocols.base import ProtocolAdapter
from app.aggregators.protocol_aggregator import (
    aggregate_portfolio_metrics_from_adapters,
)
from app.main import app
from app.schemas.defi import (
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
    StakedPosition,
)
from app.services.snapshot_aggregation import SnapshotAggregationService

# ---------------------------------------------------------------------------
# Dummy adapter & aggregator for predictable data
# ---------------------------------------------------------------------------


class _ConstAdapter(ProtocolAdapter):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    async def fetch_snapshot(self, address: str):  # noqa: D401
        return DeFiAccountSnapshot(
            user_address=address,
            timestamp=0,
            collaterals=[
                Collateral(
                    protocol=ProtocolName.aave,
                    asset="DAI",
                    amount=10,
                    usd_value=10,
                )
            ],
            borrowings=[],
            staked_positions=[
                StakedPosition(
                    protocol=ProtocolName.aave,
                    asset="AAVE",
                    amount=1,
                    usd_value=100,
                    apy=0.1,
                )
            ],
            health_scores=[HealthScore(protocol=ProtocolName.aave, score=2.0)],
            total_apy=0.1,
        )


aadapters = [_ConstAdapter("aave")]


async def _dummy_aggregator(address: str):  # noqa: D401
    return await aggregate_portfolio_metrics_from_adapters(address, aadapters)


def _override_snapshot_service(db_session: Session):
    # Provide a fake service that yields predetermined metrics.
    def _override():
        return SnapshotAggregationService(
            db_session=db_session, aggregator=_dummy_aggregator
        )

    return _override


@pytest.fixture()
def _dependency_override(db_session: Session):
    app.dependency_overrides.clear()
    # Override the newer dependency used by the timeline endpoint
    from app.api.endpoints.defi import get_portfolio_snapshot_usecase

    app.dependency_overrides[
        get_portfolio_snapshot_usecase
    ] = lambda: _DummySnapshotUsecase()
    yield
    app.dependency_overrides.clear()


def test_timeline_endpoint_with_dummy_aggregator(_dependency_override):
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/defi/timeline/0xabc?from_ts=0&to_ts=1000&raw=true")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["total_collateral_usd"] == 10


class _DummySnapshotUsecase:
    async def get_timeline(
        self,
        address: str,
        from_ts: int,
        to_ts: int,
        limit: int = 100,
        offset: int = 0,
        interval: str = "none",
    ):
        # Build a minimal PortfolioSnapshot-like dict
        return [
            {
                "user_address": address,
                "timestamp": from_ts,
                "total_collateral": 10,
                "total_borrowings": 0,
                "total_collateral_usd": 10,
                "total_borrowings_usd": 0,
                "aggregate_health_score": 2.0,
                "aggregate_apy": 0.1,
                "collaterals": [],
                "borrowings": [],
                "staked_positions": [],
                "health_scores": [],
                "protocol_breakdown": {},
            }
        ]
