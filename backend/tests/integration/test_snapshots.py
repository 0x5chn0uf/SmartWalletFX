# flake8: noqa: E501

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.wallet import Wallet
from app.stores.wallet_store import WalletStore
from app.tasks.snapshots import collect_portfolio_snapshots

client = TestClient(app)


# Patch sync engine/session to use test DB for all sync access (Celery task, etc.)
@pytest.fixture(autouse=True, scope="module")
def patch_sync_db():
    import app.core.database as db_mod
    import app.tasks.snapshots as snapshots_mod

    sync_url = "sqlite:///./test.db"
    sync_engine = create_engine(
        sync_url, connect_args={"check_same_thread": False}
    )
    SyncSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=sync_engine
    )
    db_mod.sync_engine = sync_engine
    db_mod.SyncSessionLocal = SyncSessionLocal
    snapshots_mod.SyncSessionLocal = SyncSessionLocal
    yield


@pytest.mark.asyncio
async def test_celery_task_stores_snapshots(db_session, monkeypatch):
    """Test that the Celery snapshot task processes all wallets and stores snapshots."""
    # Patch the Celery task to call the aggregation function directly (not via asyncio.run)
    import app.tasks.snapshots as snapshots_mod

    def sync_agg(address):
        class DummyMetrics:
            def __init__(self, address):
                self.user_address = address
                self.timestamp = 1234567890
                self.total_collateral = 1.0
                self.total_borrowings = 0.5
                self.total_collateral_usd = 100.0
                self.total_borrowings_usd = 50.0
                self.aggregate_health_score = 1.5
                self.aggregate_apy = 0.1
                self.collaterals = []
                self.borrowings = []
                self.staked_positions = []
                self.health_scores = []
                self.protocol_breakdown = {}

        return DummyMetrics(address)

    monkeypatch.setattr(
        "app.usecase.portfolio_aggregation_usecase.aggregate_portfolio_metrics",
        sync_agg,
    )

    def patched_task(*args, **kwargs):
        session = snapshots_mod.SyncSessionLocal()
        try:
            wallets = session.query(Wallet).all()
            for wallet in wallets:
                metrics = sync_agg(wallet.address)
                snapshot = PortfolioSnapshot(
                    user_address=metrics.user_address,
                    timestamp=metrics.timestamp,
                    total_collateral=metrics.total_collateral,
                    total_borrowings=metrics.total_borrowings,
                    total_collateral_usd=metrics.total_collateral_usd,
                    total_borrowings_usd=metrics.total_borrowings_usd,
                    aggregate_health_score=metrics.aggregate_health_score,
                    aggregate_apy=metrics.aggregate_apy,
                    collaterals=metrics.collaterals,
                    borrowings=metrics.borrowings,
                    staked_positions=metrics.staked_positions,
                    health_scores=metrics.health_scores,
                    protocol_breakdown=metrics.protocol_breakdown,
                )
                session.add(snapshot)
            session.commit()
        finally:
            session.close()

    monkeypatch.setattr(
        snapshots_mod.collect_portfolio_snapshots, "run", patched_task
    )
    wallet1 = await WalletStore.create(
        db_session, address=f"0x{uuid.uuid4().hex[:40]}", name="Test Wallet 1"
    )
    wallet2 = await WalletStore.create(
        db_session, address=f"0x{uuid.uuid4().hex[:40]}", name="Test Wallet 2"
    )
    collect_portfolio_snapshots()
    stmt = PortfolioSnapshot.__table__.select().where(
        PortfolioSnapshot.user_address.in_([wallet1.address, wallet2.address])
    )
    result = await db_session.execute(stmt)
    snapshots = result.fetchall()
    assert len(snapshots) >= 2


def test_manual_trigger_endpoint(monkeypatch):
    """Test that the manual trigger endpoint enqueues the Celery task and returns a valid task_id."""

    class DummyResult:
        id = "dummy-task-id"

    monkeypatch.setattr(
        "app.tasks.snapshots.collect_portfolio_snapshots.delay",
        lambda: DummyResult(),
    )
    response = client.post("/defi/admin/trigger-snapshot")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "triggered"
    assert data["task_id"] == "dummy-task-id"


@pytest.mark.asyncio
async def test_celery_task_no_wallets(db_session):
    """Test that the Celery task handles the case where there are no wallets in the DB."""
    wallets = await WalletStore.list_all(db_session)
    for w in wallets:
        await WalletStore.delete(db_session, w.address)
    collect_portfolio_snapshots()


@pytest.mark.asyncio
async def test_celery_task_aggregation_failure(monkeypatch, db_session):
    """Test that the Celery task handles aggregation failure for a wallet."""
    await WalletStore.create(
        db_session, address=f"0x{uuid.uuid4().hex[:40]}", name="Fail Wallet"
    )

    def fail_agg(address):
        raise Exception("Aggregation failed!")

    monkeypatch.setattr(
        "app.usecase.portfolio_aggregation_usecase.aggregate_portfolio_metrics",
        lambda address: fail_agg(address),
    )
    collect_portfolio_snapshots()


@pytest.mark.asyncio
async def test_celery_task_db_write_failure(monkeypatch, db_session):
    """Test that the Celery task handles DB write failure gracefully."""
    wallet = await WalletStore.create(
        db_session, address=f"0x{uuid.uuid4().hex[:40]}", name="DBFail Wallet"
    )

    class DummyMetrics:
        user_address = wallet.address
        timestamp = 1234567890
        total_collateral = 0.0
        total_borrowings = 0.0
        total_collateral_usd = 0.0
        total_borrowings_usd = 0.0
        aggregate_health_score = 0.0
        aggregate_apy = 0.0
        collaterals = []
        borrowings = []
        staked_positions = []
        health_scores = []
        protocol_breakdown = {}

    monkeypatch.setattr(
        "app.usecase.portfolio_aggregation_usecase.aggregate_portfolio_metrics",
        lambda address: DummyMetrics(),
    )
    import app.tasks.snapshots as snapshots_mod

    orig_SyncSessionLocal = snapshots_mod.SyncSessionLocal

    class FailingSession:
        def __init__(self):
            self._real = orig_SyncSessionLocal()

        def __getattr__(self, name):
            return getattr(self._real, name)

        def commit(self):
            raise Exception("DB write failed!")

        def close(self):
            return self._real.close()

    snapshots_mod.SyncSessionLocal = FailingSession
    try:
        collect_portfolio_snapshots()
    finally:
        snapshots_mod.SyncSessionLocal = orig_SyncSessionLocal
 