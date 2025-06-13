import pytest
from sqlalchemy import text

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.stores.portfolio_snapshot_store import PortfolioSnapshotStore
from app.usecase.portfolio_snapshot_usecase import PortfolioSnapshotUsecase


@pytest.mark.asyncio
async def test_portfolio_snapshot_usecase_cache(db_session):
    store = PortfolioSnapshotStore(db_session)
    usecase = PortfolioSnapshotUsecase(store)

    # insert snapshot records (two days)
    for ts in [1000, 2000]:
        snap = PortfolioSnapshot(
            user_address="0xabc",
            timestamp=ts,
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

    result1 = await usecase.get_timeline("0xabc", 500, 2500)
    assert len(result1) == 2

    # Second call should hit cache (no DB change) – we can verify by clearing
    # underlying table and expecting still same length via cached value.
    await db_session.execute(text("DELETE FROM portfolio_snapshots"))
    await db_session.commit()

    result2 = await usecase.get_timeline("0xabc", 500, 2500)
    assert len(result2) == 2
