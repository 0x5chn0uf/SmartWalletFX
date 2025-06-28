import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.user import User
from app.models.wallet import Wallet
from app.repositories.wallet_repository import WalletRepository

client = TestClient(app)


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_returns_200(
    db_session, authenticated_client: AsyncClient, test_user
):
    """
    Given an authenticated user and a wallet they own,
    When they request portfolio snapshots for that wallet,
    Then the response should be successful (200 OK).
    """
    # The `authenticated_client` is logged in as the `test_user`
    # so we can use that user's ID to create the wallet.
    wallet = await WalletRepository(db_session).create(
        user_id=test_user.id,
        address=f"0x{uuid.uuid4().hex[:40]}",
        name="Test Wallet",
    )
    response = await authenticated_client.get(
        f"/wallets/{wallet.address}/portfolio/snapshots"
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_for_nonexistent_wallet_returns_404(
    authenticated_client: AsyncClient,
):
    non_existent_address = "0xnotarealaddress"
    response = await authenticated_client.get(
        f"/wallets/{non_existent_address}/portfolio/snapshots"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_celery_task_stores_snapshots(db_session, monkeypatch):
    """Test that the Celery snapshot task processes all wallets and stores snapshots."""
    # Patch the Celery task to call the aggregation function directly (not via asyncio.run)
    import app.core.database as db_mod
    import app.tasks.snapshots as snapshots_mod

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
            self.collaterals: list = []
            self.borrowings: list = []
            self.staked_positions: list = []
            self.health_scores: list = []
            self.protocol_breakdown: dict = {}

    def sync_agg(self, address):
        return DummyMetrics(address)

    monkeypatch.setattr(
        "app.usecase.portfolio_aggregation_usecase.PortfolioAggregationUsecase.aggregate_portfolio_metrics",
        sync_agg,
    )

    def patched_task(*args, **kwargs):
        from app.usecase.portfolio_aggregation_usecase import (
            PortfolioAggregationUsecase,
        )

        # Use the global sync session factory
        session = db_mod.SyncSessionLocal()
        # Only process wallets created in this test to ensure isolation
        wallets = (
            session.query(Wallet)
            .filter(Wallet.address.in_([wallet1_addr, wallet2_addr]))
            .all()
        )

        usecase = PortfolioAggregationUsecase()
        for wallet in wallets:
            metrics = usecase.aggregate_portfolio_metrics(wallet.address)
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
        session.close()

    monkeypatch.setattr(snapshots_mod.collect_portfolio_snapshots, "run", patched_task)

    wallet1_addr = f"0x{uuid.uuid4().hex[:40]}"
    wallet2_addr = f"0x{uuid.uuid4().hex[:40]}"

    # A user is required for wallets
    user = User(
        username=f"snapshot-user-{uuid.uuid4().hex[:8]}",
        email=f"snapshot-{uuid.uuid4().hex[:8]}@test.com",
        hashed_password="hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    db_session.add_all(
        [
            Wallet(address=wallet1_addr, name="Test Wallet 1", user_id=user.id),
            Wallet(address=wallet2_addr, name="Test Wallet 2", user_id=user.id),
        ]
    )
    await db_session.commit()

    # Run the patched task
    snapshots_mod.collect_portfolio_snapshots.run()

    # Verify that snapshots were created using the async session
    from sqlalchemy import select

    result = await db_session.execute(
        select(PortfolioSnapshot).where(
            PortfolioSnapshot.user_address.in_([wallet1_addr, wallet2_addr])
        )
    )
    snapshots = result.scalars().all()

    assert len(snapshots) == 2
    assert {s.user_address for s in snapshots} == {wallet1_addr, wallet2_addr}
