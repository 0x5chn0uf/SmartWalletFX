import asyncio
import logging
import os
import time

from app.celery_app import celery
from app.core.database import SyncSessionLocal
from app.models.wallet import Wallet
from app.services.snapshot_aggregation import SnapshotAggregationService


@celery.task
def collect_portfolio_snapshots():
    """
    Periodically collect DeFi portfolio snapshots for all
    tracked wallet addresses.
    """
    session = SyncSessionLocal()
    try:
        # Log the DB engine URL and resolved file path
        engine_url = str(session.bind.url)
        db_file = getattr(session.bind.url, "database", None)
        abs_db_file = os.path.abspath(db_file) if db_file else None
        print(f"[Celery] SQLAlchemy engine URL: {engine_url}")
        print(f"[Celery] DB file (resolved): {abs_db_file}")
        print(
            f"[Celery] DB file exists: \
                {os.path.exists(abs_db_file) if abs_db_file else 'N/A'}"
        )
        start = time.time()
        wallets = session.query(Wallet).all()
        success = 0
        errors = 0
        service = SnapshotAggregationService(session)
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
            f"[Celery] Snapshot job complete. \
                Success: {success}, Errors: {errors}, \
                Time: {elapsed:.2f}s"
        )
    finally:
        session.close()
