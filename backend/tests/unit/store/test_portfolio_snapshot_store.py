import pytest

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.stores.portfolio_snapshot_store import PortfolioSnapshotStore


@pytest.mark.asyncio
async def test_create_and_get_snapshot(db_session):
    store = PortfolioSnapshotStore(db_session)
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
    created = await store.create_snapshot(snapshot)
    assert created.id is not None
    # Retrieve by address and range
    results = await store.get_snapshots_by_address_and_range(
        "0xabc", 900, 1100
    )
    assert len(results) == 1
    assert results[0].user_address == "0xabc"
    # Retrieve latest
    latest = await store.get_latest_snapshot_by_address("0xabc")
    assert latest.timestamp == 1000


@pytest.mark.asyncio
async def test_get_snapshots_by_address_and_range_multiple(db_session):
    store = PortfolioSnapshotStore(db_session)
    # Insert multiple snapshots
    for ts in [1000, 2000, 3000]:
        snap = PortfolioSnapshot(
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
        await store.create_snapshot(snap)
    results = await store.get_snapshots_by_address_and_range(
        "0xdef", 1500, 3500
    )
    assert len(results) == 2
    assert results[0].timestamp == 2000
    assert results[1].timestamp == 3000
    latest = await store.get_latest_snapshot_by_address("0xdef")
    assert latest.timestamp == 3000
