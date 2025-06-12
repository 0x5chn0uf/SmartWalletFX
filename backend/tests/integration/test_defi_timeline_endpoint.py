import asyncio

import pytest
import sqlalchemy
from fastapi import status
from httpx import AsyncClient

from app.core.database import engine, get_db
from app.main import app
from app.models.portfolio_snapshot import PortfolioSnapshot


@pytest.fixture(autouse=True, scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop


@pytest.fixture(scope="module")
async def setup_db():
    # Assume Alembic has already migrated the schema
    yield


@pytest.fixture(autouse=True)
def override_get_db(db_session):
    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_timeline_empty_result(db_session):
    print("SQLAlchemy engine URL:", str(engine.url))
    await db_session.execute(sqlalchemy.delete(PortfolioSnapshot))
    await db_session.commit()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get(
            "/defi/timeline/0xnotfound?from_ts=1000&to_ts=2000"
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
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Query full range
        resp = await ac.get("/defi/timeline/0xtest?from_ts=900&to_ts=2100")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 2
        assert data[0]["timestamp"] == 1000
        assert data[1]["timestamp"] == 2000
        # Query partial range
        resp = await ac.get("/defi/timeline/0xtest?from_ts=1500&to_ts=2100")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == 2000
        # Query out of range
        resp = await ac.get("/defi/timeline/0xtest?from_ts=2101&to_ts=3000")
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
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Default: should return all
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100"
        )
        data = resp.json()
        assert len(data) == 3
        # Limit=1
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=1"
        )
        data = resp.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == 1000
        # Offset=1, limit=1
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=1&offset=1"
        )
        data = resp.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == 2000
        # Offset=2, limit=2 (should only get last)
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=2&offset=2"
        )
        data = resp.json()
        assert len(data) == 1
        assert data[0]["timestamp"] == 3000
        # Offset beyond available
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=2&offset=5"
        )
        data = resp.json()
        assert data == []
        # Negative values (should treat as 0 or error)
        resp = await ac.get(
            "/defi/timeline/0xpaginated?from_ts=900&to_ts=3100&limit=-1&offset=-1"
        )
        assert resp.status_code == 422 or len(resp.json()) == 3
