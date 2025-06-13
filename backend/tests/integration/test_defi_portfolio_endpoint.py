from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import AsyncClient

from app.main import app
from app.schemas.defi import Borrowing, Collateral, HealthScore, StakedPosition

TEST_ADDRESS = "0x1111111111111111111111111111111111111111"


@pytest.mark.asyncio
@patch(
    "app.usecase.portfolio_aggregation_usecase.get_aave_user_snapshot_usecase",  # noqa: E501
    new_callable=AsyncMock,
)
@patch(
    "app.usecase.portfolio_aggregation_usecase.get_compound_user_snapshot_usecase",  # noqa: E501
    new_callable=AsyncMock,
)
@patch(
    "app.usecase.portfolio_aggregation_usecase.get_radiant_user_snapshot_usecase",  # noqa: E501
    new_callable=AsyncMock,
)
async def test_get_portfolio_metrics_success(
    mock_radiant, mock_compound, mock_aave
):
    # Use real Pydantic models for mock data
    class Dummy:
        pass

    aave_snap = Dummy()
    aave_snap.collaterals = [
        Collateral(protocol="AAVE", asset="DAI", amount=1000, usd_value=1000)
    ]
    aave_snap.borrowings = [
        Borrowing(
            protocol="AAVE",
            asset="DAI",
            amount=200,
            usd_value=200,
            interest_rate=None,
        )
    ]
    aave_snap.staked_positions = [
        StakedPosition(
            protocol="AAVE", asset="DAI", amount=1000, usd_value=1000, apy=0.04
        )
    ]
    aave_snap.health_scores = [HealthScore(protocol="AAVE", score=2.1)]
    aave_snap.user_address = "0x123"
    aave_snap.timestamp = 0
    aave_snap.total_apy = 0.04
    compound_snap = Dummy()
    compound_snap.collaterals = [
        Collateral(
            protocol="COMPOUND", asset="USDC", amount=500, usd_value=500
        )
    ]
    compound_snap.borrowings = [
        Borrowing(
            protocol="COMPOUND",
            asset="ETH",
            amount=0.5,
            usd_value=0.5,
            interest_rate=None,
        )
    ]
    compound_snap.staked_positions = []
    compound_snap.health_scores = [HealthScore(protocol="COMPOUND", score=1.8)]
    compound_snap.user_address = "0x123"
    compound_snap.timestamp = 0
    compound_snap.total_apy = None
    mock_aave.return_value = aave_snap
    mock_compound.return_value = compound_snap
    mock_radiant.return_value = None
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/defi/portfolio/0x123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_collateral"] == 1500
    assert data["total_collateral_usd"] == 1500
    assert abs(data["total_borrowings"] - 200.5) < 1e-6
    assert abs(data["total_borrowings_usd"] - 200.5) < 1e-6
    assert abs(data["aggregate_health_score"] - 1.95) < 1e-6
    assert abs(data["aggregate_apy"] - 0.04) < 1e-6
    assert len(data["collaterals"]) == 2
    assert len(data["borrowings"]) == 2
    assert len(data["staked_positions"]) == 1
    assert len(data["health_scores"]) == 2
    pb = data["protocol_breakdown"]
    assert set(pb.keys()) == {"aave", "compound", "radiant"}
    assert pb["aave"]["total_collateral"] == 1000
    assert pb["compound"]["total_collateral"] == 500
    assert pb["radiant"]["total_collateral"] == 0
    assert pb["aave"]["total_borrowings"] == 200
    assert abs(pb["compound"]["total_borrowings"] - 0.5) < 1e-6
    assert pb["radiant"]["total_borrowings"] == 0
    assert "timestamp" in data
    assert data["historical_snapshots"] is None


@pytest.mark.asyncio
@patch(
    "app.usecase.portfolio_aggregation_usecase.get_aave_user_snapshot_usecase",  # noqa: E501
    new_callable=AsyncMock,
)
@patch(
    "app.usecase.portfolio_aggregation_usecase.get_compound_user_snapshot_usecase",  # noqa: E501
    new_callable=AsyncMock,
)
@patch(
    "app.usecase.portfolio_aggregation_usecase.get_radiant_user_snapshot_usecase",  # noqa: E501
    new_callable=AsyncMock,
)
async def test_get_portfolio_metrics_all_none(
    mock_radiant, mock_compound, mock_aave
):
    mock_aave.return_value = None
    mock_compound.return_value = None
    mock_radiant.return_value = None
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/defi/portfolio/0xdead")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_collateral"] == 0
    assert data["total_collateral_usd"] == 0
    assert data["total_borrowings"] == 0
    assert data["total_borrowings_usd"] == 0
    assert data["aggregate_health_score"] is None
    assert data["aggregate_apy"] is None
    assert data["collaterals"] == []
    assert data["borrowings"] == []
    assert data["staked_positions"] == []
    assert data["health_scores"] == []
    pb = data["protocol_breakdown"]
    assert set(pb.keys()) == {"aave", "compound", "radiant"}
    for v in pb.values():
        assert v["total_collateral"] == 0
        assert v["total_borrowings"] == 0
        assert v["aggregate_health_score"] is None
        assert v["aggregate_apy"] is None
        assert v["collaterals"] == []
        assert v["borrowings"] == []
        assert v["staked_positions"] == []
        assert v["health_scores"] == []
    assert "timestamp" in data
    assert data["historical_snapshots"] is None


@pytest.mark.asyncio
async def test_portfolio_metrics_endpoint(monkeypatch, test_app):
    """Portfolio metrics endpoint returns our stubbed aggregation."""
    from datetime import datetime

    from app.usecase.portfolio_aggregation_usecase import PortfolioMetrics

    async def _mock_agg(address: str):  # noqa: D401
        return PortfolioMetrics(
            user_address=address,
            total_collateral=0.0,
            total_borrowings=0.0,
            total_collateral_usd=0.0,
            total_borrowings_usd=0.0,
            aggregate_health_score=None,
            aggregate_apy=None,
            collaterals=[],
            borrowings=[],
            staked_positions=[],
            health_scores=[],
            protocol_breakdown={},
            historical_snapshots=None,
            timestamp=datetime.utcnow(),
        )

    monkeypatch.setattr(
        "app.api.endpoints.defi.aggregate_portfolio_metrics", _mock_agg
    )

    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        resp = await ac.get(f"/defi/portfolio/{TEST_ADDRESS}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_address"].lower() == TEST_ADDRESS.lower()
