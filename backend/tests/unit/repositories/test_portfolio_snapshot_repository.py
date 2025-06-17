import datetime as _dt

import pytest

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.repositories.portfolio_snapshot_repository import (
    PortfolioSnapshotRepository,
)


@pytest.mark.asyncio
async def test_create_and_get_snapshot(db_session):
    repo = PortfolioSnapshotRepository(db_session)
    snapshot = PortfolioSnapshot(
        user_address="0xabc",
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
    created = await repo.create_snapshot(snapshot)
    assert created.id is not None
    results = await repo.get_snapshots_by_address_and_range("0xabc", 900, 1100)
    assert len(results) == 1 and results[0].user_address == "0xabc"
    latest = await repo.get_latest_snapshot_by_address("0xabc")
    assert latest.timestamp == 1000


@pytest.mark.asyncio
async def test_get_snapshots_by_address_and_range_multiple(db_session):
    repo = PortfolioSnapshotRepository(db_session)
    for ts in [1000, 2000, 3000]:
        await repo.create_snapshot(
            PortfolioSnapshot(
                user_address="0xdef",
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
        )
    results = await repo.get_snapshots_by_address_and_range("0xdef", 1500, 3500)
    assert [s.timestamp for s in results] == [2000, 3000]
    assert (await repo.get_latest_snapshot_by_address("0xdef")).timestamp == 3000


# ---------------------------------------------------------------------------
# Extra tests (CRUD helpers, timeline, cache)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_portfolio_snapshot_repository_crud_and_helpers(db_session):
    repo = PortfolioSnapshotRepository(db_session)
    snap = PortfolioSnapshot(
        user_address="0xabc",
        timestamp=100,
        total_collateral=1.0,
        total_borrowings=0.5,
        total_collateral_usd=1.0,
        total_borrowings_usd=0.5,
        aggregate_health_score=None,
        aggregate_apy=None,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
    )
    created = await repo.create_snapshot(snap)
    assert created.id is not None
    assert (await repo.get_latest_snapshot_by_address("0xabc")).id == created.id
    in_range = await repo.get_snapshots_by_address_and_range("0xabc", 0, 200)
    assert len(in_range) == 1
    await repo.delete_snapshot(created.id)
    assert await repo.get_latest_snapshot_by_address("0xabc") is None


@pytest.mark.asyncio
async def test_portfolio_snapshot_repository_timeline_intervals(db_session):
    repo = PortfolioSnapshotRepository(db_session)
    base_ts = int(_dt.datetime(2023, 1, 2, 12, 0, tzinfo=_dt.timezone.utc).timestamp())
    for i in range(14):
        await repo.create_snapshot(
            PortfolioSnapshot(
                user_address="0xabc",
                timestamp=base_ts + i * 86_400,
                total_collateral=1.0,
                total_borrowings=0.5,
                total_collateral_usd=1.0,
                total_borrowings_usd=0.5,
                aggregate_health_score=1.0,
                aggregate_apy=None,
                collaterals=[],
                borrowings=[],
                staked_positions=[],
                health_scores=[],
                protocol_breakdown={},
            )
        )
    end_ts = base_ts + 13 * 86_400
    assert len(await repo.get_timeline("0xabc", base_ts, end_ts, interval="none")) == 14
    assert (
        len(await repo.get_timeline("0xabc", base_ts, end_ts, interval="daily")) == 14
    )
    assert (
        len(await repo.get_timeline("0xabc", base_ts, end_ts, interval="weekly")) == 2
    )
    with pytest.raises(ValueError):
        await repo.get_timeline("0xabc", base_ts, end_ts, interval="hourly")


@pytest.mark.asyncio
async def test_portfolio_snapshot_repository_cache(db_session):
    repo = PortfolioSnapshotRepository(db_session)
    params = {
        "user_address": "0xabc",
        "from_ts": 0,
        "to_ts": 100,
        "interval": "none",
        "limit": 10,
        "offset": 0,
    }
    await repo.set_cache(
        **params,
        response_json='{"ok": true}',
        expires_in_seconds=3600,
    )
    assert await repo.get_cache(**params) == '{"ok": true}'
    await repo.set_cache(
        **params,
        response_json='{"expired": true}',
        expires_in_seconds=-1,
    )
    assert await repo.get_cache(**params) is None
