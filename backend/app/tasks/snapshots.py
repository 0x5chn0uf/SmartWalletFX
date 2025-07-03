import asyncio
import os
import time

import structlog

from app.celery_app import celery
from app.di import get_session_sync
from app.models.wallet import Wallet
from app.services.snapshot_aggregation import SnapshotAggregationService
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioAggregationUsecase,
)

logger = structlog.get_logger(__name__)


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
    task_start_time = time.time()

    logger.info("Portfolio snapshot collection task started")

    session = get_session_sync()
    try:
        # Log the DB engine URL and resolved file path
        engine_url = str(session.bind.url)
        db_file = getattr(session.bind.url, "database", None)
        abs_db_file = os.path.abspath(db_file) if db_file else None

        logger.debug(
            "Database configuration",
            engine_url=engine_url,
            db_file=abs_db_file,
            db_file_exists=os.path.exists(abs_db_file) if abs_db_file else None,
        )

        start = time.time()
        wallets = session.query(Wallet).all()

        logger.info(
            "Retrieved wallets for snapshot collection", wallet_count=len(wallets)
        )

        success = 0
        errors = 0
        aggregator = _build_aggregator()
        service = SnapshotAggregationService(session, aggregator)

        for wallet in wallets:
            wallet_start_time = time.time()
            try:
                logger.debug(
                    "Processing wallet snapshot",
                    wallet_address=wallet.address,
                    wallet_id=wallet.id,
                )

                service.save_snapshot_sync(wallet.address)
                session.commit()

                wallet_duration = int((time.time() - wallet_start_time) * 1000)
                logger.info(
                    "Snapshot stored successfully",
                    wallet_address=wallet.address,
                    wallet_id=wallet.id,
                    duration_ms=wallet_duration,
                )
                success += 1
            except Exception as e:
                session.rollback()
                wallet_duration = int((time.time() - wallet_start_time) * 1000)
                logger.error(
                    "Error processing wallet snapshot",
                    wallet_address=wallet.address,
                    wallet_id=wallet.id,
                    duration_ms=wallet_duration,
                    error=str(e),
                    exc_info=True,
                )
                errors += 1

        elapsed = time.time() - start
        total_duration = int((time.time() - task_start_time) * 1000)

        logger.info(
            "Portfolio snapshot collection task completed",
            total_wallets=len(wallets),
            successful_snapshots=success,
            failed_snapshots=errors,
            processing_time_ms=int(elapsed * 1000),
            total_duration_ms=total_duration,
        )
    except Exception as exc:
        total_duration = int((time.time() - task_start_time) * 1000)
        logger.error(
            "Portfolio snapshot collection task failed",
            total_duration_ms=total_duration,
            error=str(exc),
            exc_info=True,
        )
        raise
    finally:
        session.close()
