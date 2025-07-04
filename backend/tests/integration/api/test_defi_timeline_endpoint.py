# flake8: noqa: E501

import httpx
import pytest
import sqlalchemy
from fastapi import status
from httpx import AsyncClient

from app.core.database import engine
from app.main import app
from app.models.portfolio_snapshot import PortfolioSnapshot


@pytest.mark.asyncio
async def test_timeline_empty_result(db_session):
    print("SQLAlchemy engine URL:", str(engine.url))
    await db_session.execute(sqlalchemy.delete(PortfolioSnapshot))
    await db_session.commit()
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/defi/timeline/0xnotfound?from_ts=1000&to_ts=2000&raw=true"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []


@pytest.mark.asyncio
async def test_timeline_insert_and_retrieve(db_session):
    await db_session.execute(sqlalchemy.delete(PortfolioSnapshot))
    await db_session.commit()
    # Insert test data
    snap1 = PortfolioSnapshot(
        user_address="0xtest",
        timestamp=1000,
        total_collateral=1.0,
        total_borrowings=0.5,
        total_collateral_usd=1.1,
        total_borrowings_usd=0.6,
        aggregate_health_score=0.9,
        aggregate_apy=0.05,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
    )
    snap2 = PortfolioSnapshot(
        user_address="0xtest",
        timestamp=2000,
        total_collateral=2.0,
        total_borrowings=1.0,
        total_collateral_usd=2.2,
        total_borrowings_usd=1.2,
        aggregate_health_score=0.8,
        aggregate_apy=0.06,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
    )
    db_session.add_all([snap1, snap2])
    await db_session.commit()
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Query full range
        resp = await ac.get("/defi/timeline/0xtest?from_ts=900&to_ts=2100&raw=true")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 2
        assert data[0]["timestamp"] == 1000
        assert data[1]["timestamp"] == 2000
        # Query partial range
        resp = await ac.get("/defi/timeline/0xtest?from_ts=1500&to_ts=2100&raw=true")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == 2000
        # Query out of range
        resp = await ac.get("/defi/timeline/0xtest?from_ts=2101&to_ts=3000&raw=true")
        assert resp.json() == []


@pytest.mark.asyncio
async def test_timeline_pagination_and_limits(db_session):
    await db_session.execute(sqlalchemy.delete(PortfolioSnapshot))
    await db_session.commit()
    # Insert 3 test snapshots
    for ts in [1000, 2000, 3000]:
        snap = PortfolioSnapshot(
            user_address="0xpaginated",
            timestamp=ts,
            total_collateral=ts,
            total_borrowings=0.0,
            total_collateral_usd=ts,
            total_borrowings_usd=0.0,
            aggregate_health_score=None,
            aggregate_apy=None,
            collaterals=[],
            borrowings=[],
            staked_positions=[],
            health_scores=[],
            protocol_breakdown={},
        )
        db_session.add(snap)
    await db_session.commit()
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Default: should return all
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&raw=true"
        )
        data = resp.json()
        assert len(data) == 3
        # Limit=1
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=1&raw=true"
        )
        data = resp.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == 1000
        # Offset=1, limit=1
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=1&offset=1&raw=true"
        )
        data = resp.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == 2000
        # Offset=2, limit=2 (should only get last)
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=2&offset=2&raw=true"
        )
        data = resp.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == 3000
        # Offset beyond available
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=2&offset=5&raw=true"
        )
        data = resp.json()
        assert data == []
        # Negative values (should treat as 0 or error)
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=-1&offset=-1&raw=true"
        )
        assert resp.status_code == 422 or len(resp.json()) == 3


@pytest.mark.asyncio
async def test_timeline_response_wrapper_metadata(db_session):
    """Verify /defi/timeline default response contains metadata fields."""
    await db_session.execute(sqlalchemy.delete(PortfolioSnapshot))
    await db_session.commit()
    snap = PortfolioSnapshot(
        user_address="0xmeta",
        timestamp=1000,
        total_collateral=1.0,
        total_borrowings=0.0,
        total_collateral_usd=1.0,
        total_borrowings_usd=0.0,
        aggregate_health_score=None,
        aggregate_apy=None,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
    )
    db_session.add(snap)
    await db_session.commit()
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/defi/timeline/0xmeta?from_ts=900&to_ts=1100")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert set(body.keys()) == {
            "snapshots",
            "interval",
            "limit",
            "offset",
            "total",
        }
        assert body["total"] == 1
        assert len(body["snapshots"]) == 1


@pytest.mark.asyncio
async def test_timeline_response_metadata(db_session):
    # ensure at least one snapshot exists
    await db_session.execute(sqlalchemy.delete(PortfolioSnapshot))
    await db_session.commit()
    snap = PortfolioSnapshot(
        user_address="0xmeta",
        timestamp=1234,
        total_collateral=1,
        total_borrowings=0,
        total_collateral_usd=1,
        total_borrowings_usd=0,
        aggregate_health_score=None,
        aggregate_apy=None,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
    )
    db_session.add(snap)
    await db_session.commit()

    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/defi/timeline/0xmeta?from_ts=1000&to_ts=2000")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["interval"] == "none"
        assert payload["limit"] == 100
        assert payload["total"] >= 1
        assert isinstance(payload["snapshots"], list)
        assert payload["snapshots"][0]["user_address"] == "0xmeta"


@pytest.mark.asyncio
async def test_portfolio_timeline_and_admin_trigger(monkeypatch, test_app):
    """Timeline endpoint with mocked usecase & Celery admin trigger."""
    from types import SimpleNamespace

    # Mock the timeline usecase
    async def _mock_get_portfolio_snapshot_usecase(db):  # noqa: D401
        class _DummyUsecase:
            async def get_timeline(  # noqa: D401  # pylint: disable=unused-argument
                self,
                address,
                from_ts,
                to_ts,
                limit=100,
                offset=0,
                interval="none",
            ):
                return []

        return _DummyUsecase()

    monkeypatch.setattr(
        "app.api.endpoints.defi.get_portfolio_snapshot_usecase",
        _mock_get_portfolio_snapshot_usecase,
    )

    # Mock Celery task delay to return object with id attribute
    mock_result = SimpleNamespace(id="mock-task-id")

    def _mock_send_task(name):  # noqa: D401
        assert name == "app.tasks.snapshots.collect_portfolio_snapshots"
        return mock_result

    monkeypatch.setattr("app.api.endpoints.defi.celery.send_task", _mock_send_task)

    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Timeline request
        timeline_resp = await ac.get(
            "/defi/timeline/0x1111111111111111111111111111111111111111",
            params={"from_ts": 1, "to_ts": 2},
        )

        # Admin trigger request
        trigger_resp = await ac.post("/defi/admin/trigger-snapshot")

    assert timeline_resp.status_code == 200
    assert timeline_resp.json()["total"] == 0

    assert trigger_resp.status_code == 200
    assert trigger_resp.json() == {
        "status": "triggered",
        "task_id": "mock-task-id",
    }
