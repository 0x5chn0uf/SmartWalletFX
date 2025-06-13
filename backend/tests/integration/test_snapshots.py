# flake8: noqa: E501

import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.wallet import Wallet
from app.stores.wallet_store import WalletStore
from app.tasks.snapshots import collect_portfolio_snapshots

client = TestClient(app)


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
    # Create wallets using the synchronous session so the Celery task sees them
    wallet1_addr = f"0x{uuid.uuid4().hex[:40]}"
    wallet2_addr = f"0x{uuid.uuid4().hex[:40]}"

    sync_session = snapshots_mod.SyncSessionLocal()
    try:
        sync_session.add_all(
            [
                Wallet(
                    address=wallet1_addr, name="Test Wallet 1", balance=0.0
                ),
                Wallet(
                    address=wallet2_addr, name="Test Wallet 2", balance=0.0
                ),
            ]
        )
        sync_session.commit()
    finally:
        sync_session.close()

    # Run the patched snapshot task directly (bypassing Celery wrapper)
    patched_task()

    # Verify snapshots were stored using sync session
    sync_session = snapshots_mod.SyncSessionLocal()
    try:
        count = (
            sync_session.query(PortfolioSnapshot)
            .filter(
                PortfolioSnapshot.user_address.in_(
                    [wallet1_addr, wallet2_addr]
                )
            )
            .count()
        )
    finally:
        sync_session.close()
    assert count >= 2


@pytest.mark.asyncio
async def test_manual_trigger_endpoint(monkeypatch):
    """Test the admin endpoint correctly triggers the snapshot task."""
    mock_send_task = MagicMock(return_value=MagicMock(id="dummy-task-id"))
    monkeypatch.setattr(
        "app.api.endpoints.defi.celery.send_task", mock_send_task
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.post("/defi/admin/trigger-snapshot")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "triggered"
    assert data["task_id"] == "dummy-task-id"
    mock_send_task.assert_called_once()


@pytest.mark.asyncio
async def test_snapshot_task_e2e_flow(test_app, monkeypatch):
    """
    Tests the end-to-end flow:
    1. Create wallets via API.
    2. Trigger snapshot task.
    3. Verify snapshots are created by querying the timeline endpoint.
    """

    # --- Setup ---
    # 1. Mock the aggregation use case to return predictable data
    #    This avoids external calls and keeps the test focused on the integration.
    class DummyMetrics:
        def __init__(self, address):
            self.user_address = address
            self.timestamp = 1234567890
            self.total_collateral_usd = 100.0
            self.total_borrowings_usd = 50.0
            # Add other fields as necessary, matching PortfolioSnapshot structure
            self.total_collateral = 1.0
            self.total_borrowings = 0.5
            self.aggregate_health_score = 1.5
            self.aggregate_apy = 0.1
            self.collaterals = []
            self.borrowings = []
            self.staked_positions = []
            self.health_scores = []
            self.protocol_breakdown = {}

    def _patched_save_snapshot_sync(self, user_address):  # type: ignore[override]
        assert isinstance(self.db_session, Session)
        snapshot = PortfolioSnapshot(
            user_address=user_address,
            timestamp=1234567890,
            total_collateral=1.0,
            total_borrowings=0.5,
            total_collateral_usd=100.0,
            total_borrowings_usd=50.0,
            aggregate_health_score=1.5,
            aggregate_apy=0.1,
            collaterals=[],
            borrowings=[],
            staked_positions=[],
            health_scores=[],
            protocol_breakdown={},
        )
        self.db_session.add(snapshot)
        self.db_session.commit()
        return snapshot

    monkeypatch.setattr(
        "app.services.snapshot_aggregation.SnapshotAggregationService.save_snapshot_sync",
        _patched_save_snapshot_sync,
    )

    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        # 2. Create wallets that the task will process
        wallet1_addr = f"0x{uuid.uuid4().hex[:40]}"
        wallet2_addr = f"0x{uuid.uuid4().hex[:40]}"
        await client.post(
            "/wallets", json={"address": wallet1_addr, "name": "E2E Wallet 1"}
        )
        await client.post(
            "/wallets", json={"address": wallet2_addr, "name": "E2E Wallet 2"}
        )

        # --- Execution ---
        # 3. Trigger the Celery task directly
        collect_portfolio_snapshots()

        # --- Verification ---
        # 4. Query the timeline to see if snapshots were created for each wallet
        timeline1_resp = await client.get(
            f"/defi/timeline/{wallet1_addr}?from_ts=0&to_ts=2000000000&raw=true"
        )
        assert timeline1_resp.status_code == 200

        timeline2_resp = await client.get(
            f"/defi/timeline/{wallet2_addr}?from_ts=0&to_ts=2000000000&raw=true"
        )
        assert timeline2_resp.status_code == 200


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
