import logging
import os
import time
import asyncio

from app.celery_app import celery
from app.di import get_session_sync
from app.models.wallet import Wallet
from app.services.snapshot_aggregation import SnapshotAggregationService
from app.usecase.portfolio_aggregation_usecase import PortfolioAggregationUsecase

def _build_aggregator():
    """Create an aggregation callable bound to default adapters list."""
    usecase = PortfolioAggregationUsecase()

    def _aggregator(address: str):
        return asyncio.run(usecase.aggregate_portfolio_metrics(address))

    return _aggregator

@celery.task
def collect_portfolio_snapshots():
    """
    Periodically collect DeFi portfolio snapshots for all
    tracked wallet addresses.
    """
    session = get_session_sync()
    try:
        # Log the DB engine URL and resolved file path
        engine_url = str(session.bind.url)
        db_file = getattr(session.bind.url, "database", None)
        abs_db_file = os.path.abspath(db_file) if db_file else None
        print(f"[Celery] SQLAlchemy engine URL: {engine_url}")
        print(f"[Celery] DB file (resolved): {abs_db_file}")
        print(
            f"[Celery] DB file exists: "
            f"{os.path.exists(abs_db_file) if abs_db_file else 'N/A'}"
        )

        start = time.time()
        wallets = session.query(Wallet).all()
        success = 0
        errors = 0
        aggregator = _build_aggregator()
        service = SnapshotAggregationService(session, aggregator)
        for wallet in wallets:
            try:
                service.save_snapshot_sync(wallet.address)
                session.commit()
                logging.info(
                    f"[Celery] Snapshot stored for wallet: {wallet.address}"
                )
                success += 1
            except Exception as e:
                session.rollback()
                logging.error(
                    f"[Celery] Error processing wallet {wallet.address}: {e}"
                )
                errors += 1

        elapsed = time.time() - start
        print(
            f"[Celery] Snapshot job complete. "
            f"Success: {success}, Errors: {errors}, "
            f"Time: {elapsed:.2f}s"
        )
    finally:
        session.close()
