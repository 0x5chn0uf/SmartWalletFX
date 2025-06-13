from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base  # imported lazily to avoid heavy import earlier
from app.services.snapshot_aggregation import SnapshotAggregationService

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def fake_metrics(user_address: str):  # sync fake aggregator
    return SimpleNamespace(
        user_address=user_address,
        timestamp=SimpleNamespace(timestamp=lambda: 1234567890),
        total_collateral=1.0,
        total_borrowings=0.5,
        total_collateral_usd=1.0,
        total_borrowings_usd=0.5,
        aggregate_health_score=1.2,
        aggregate_apy=0.04,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
    )


def test_save_snapshot_sync_requires_sync_session(sync_session):
    service = SnapshotAggregationService(sync_session, aggregator=fake_metrics)
    # Should not raise TypeError when using sync session
    snapshot = service.save_snapshot_sync("0xABC")
    assert snapshot.user_address == "0xABC"


@pytest.mark.asyncio
async def test_save_snapshot_with_sync_session_raises(sync_session):
    service = SnapshotAggregationService(sync_session, aggregator=fake_metrics)
    with pytest.raises(TypeError):
        await service.save_snapshot("0xABC")


def test_save_snapshot_sync_with_async_aggregator(sync_session):
    async def async_fake(user_address: str):
        return fake_metrics(user_address)

    service = SnapshotAggregationService(
        sync_session, aggregator=async_fake
    )  # type: ignore
    snapshot = service.save_snapshot_sync("0xDEF")
    assert snapshot.user_address == "0xDEF"


@pytest.mark.asyncio
async def test_build_snapshot_async():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:

        async def async_aggr(addr: str):
            return fake_metrics(addr)

        service = SnapshotAggregationService(
            session, aggregator=async_aggr
        )  # type: ignore
        snapshot = await service.build_snapshot("0xAAA")
        assert snapshot.user_address == "0xAAA"
    await engine.dispose()


def test_metrics_to_snapshot_mapping():
    metrics = fake_metrics("0xZZ")
    snapshot = SnapshotAggregationService._metrics_to_snapshot(
        metrics
    )  # type: ignore
    assert snapshot.user_address == "0xZZ"
    assert snapshot.total_collateral == 1.0
    assert snapshot.total_borrowings == 0.5
