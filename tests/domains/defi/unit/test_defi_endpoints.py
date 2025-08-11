import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Request, status

from app.api.endpoints.defi import DeFi
from app.domain.schemas.defi import PortfolioSnapshot
from app.domain.schemas.defi_dashboard import DefiKPI
from app.domain.schemas.portfolio_metrics import PortfolioMetrics
from app.domain.schemas.portfolio_timeline import PortfolioTimeline
from app.domain.schemas.wallet import WalletResponse


@pytest.fixture
def mock_wallet_uc():
    """A WalletUsecase mock with async methods stubbed out."""
    uc = AsyncMock()
    DeFi(uc)  # inject singleton dependency for the staticmethods
    return uc


@pytest.fixture
def fake_request() -> Request:
    req = SimpleNamespace()
    req.client = SimpleNamespace(host="unit-test")
    return req  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_timeline_endpoint_success(mock_wallet_uc, fake_request):
    addr = "0x" + "a" * 40
    uid = uuid.uuid4()

    # Mock timeline return value
    tl = PortfolioTimeline(
        timestamps=[1, 2], collateral_usd=[100.0, 120.0], borrowings_usd=[50.0, 60.0]
    )
    mock_wallet_uc.get_portfolio_timeline.return_value = tl

    with patch("app.api.endpoints.defi.get_user_id_from_request", return_value=uid):
        res = await DeFi.get_portfolio_timeline_for_address(fake_request, addr)

    assert res == tl
    mock_wallet_uc.get_portfolio_timeline.assert_awaited_once_with(
        uid, addr, "daily", 30, 0, None, None
    )


@pytest.mark.asyncio
async def test_timeline_endpoint_with_date_range(mock_wallet_uc, fake_request):
    addr = "0x" + "a" * 40
    uid = uuid.uuid4()

    # Mock timeline return value for date range
    tl = PortfolioTimeline(
        timestamps=[1640995200, 1641081600], # Jan 1-2, 2022
        collateral_usd=[200.0, 250.0], 
        borrowings_usd=[100.0, 120.0]
    )
    mock_wallet_uc.get_portfolio_timeline.return_value = tl

    with patch("app.api.endpoints.defi.get_user_id_from_request", return_value=uid):
        res = await DeFi.get_portfolio_timeline_for_address(
            fake_request, addr, "daily", 30, 0, "2022-01-01", "2022-01-02"
        )

    assert res == tl
    mock_wallet_uc.get_portfolio_timeline.assert_awaited_once_with(
        uid, addr, "daily", 30, 0, "2022-01-01", "2022-01-02"
    )


@pytest.mark.asyncio
async def test_snapshot_endpoint_aggregation(mock_wallet_uc, fake_request):
    uid = uuid.uuid4()

    # Two wallets with simple metrics
    w1 = WalletResponse(
        id=uuid.uuid4(),
        address="0x" + "b" * 40,
        name="w1",
        user_id=uid,
        is_active=True,
        balance_usd=0,
    )
    w2 = WalletResponse(
        id=uuid.uuid4(),
        address="0x" + "c" * 40,
        name="w2",
        user_id=uid,
        is_active=True,
        balance_usd=0,
    )
    mock_wallet_uc.list_wallets.return_value = [w1, w2]

    metrics1 = PortfolioMetrics(
        user_address=w1.address,
        timestamp=1,
        total_collateral=100.0,
        total_borrowings=40.0,
        total_collateral_usd=150.0,
        total_borrowings_usd=60.0,
        aggregate_health_score=0.9,
        aggregate_apy=4.0,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
    )
    metrics2 = PortfolioMetrics(
        user_address=w2.address,
        timestamp=1,
        total_collateral=50.0,
        total_borrowings=20.0,
        total_collateral_usd=75.0,
        total_borrowings_usd=30.0,
        aggregate_health_score=0.8,
        aggregate_apy=6.0,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
    )

    async def _metrics(uid_arg, addr_arg):
        return metrics1 if addr_arg == w1.address else metrics2

    mock_wallet_uc.get_portfolio_metrics.side_effect = _metrics

    with patch("app.api.endpoints.defi.get_user_id_from_request", return_value=uid):
        snapshot: PortfolioSnapshot = await DeFi.get_current_portfolio_snapshot(
            fake_request
        )

    # When health_scores & staked_positions empty, aggregate scores may be None
    assert snapshot.total_collateral_usd == 225.0
    assert snapshot.total_borrowings_usd == 90.0


@pytest.mark.asyncio
async def test_kpi_endpoint_uses_snapshot(fake_request):
    uid = uuid.uuid4()

    fake_snapshot = PortfolioSnapshot(
        user_address="agg",
        timestamp=1,
        total_collateral=0.0,
        total_borrowings=0.0,
        total_collateral_usd=200.0,
        total_borrowings_usd=0.0,
        aggregate_health_score=None,
        aggregate_apy=5.0,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
    )

    with patch(
        "app.api.endpoints.defi.get_user_id_from_request", return_value=uid
    ), patch(
        "app.api.endpoints.defi.DeFi.get_current_portfolio_snapshot",
        return_value=fake_snapshot,
    ):
        kpi: DefiKPI = await DeFi.get_portfolio_kpi(fake_request)

    assert kpi.tvl == 200.0
    assert kpi.apy == 5.0
    assert kpi.protocols == []
