from __future__ import annotations

"""Snapshot aggregation service.

Transforms aggregated portfolio metrics into PortfolioSnapshot ORM objects
and optionally persists them. Designed for dependency-injection and reuse
across FastAPI endpoints and Celery tasks.
"""
import asyncio
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioMetrics,
    aggregate_portfolio_metrics,
)

# Type alias for injected aggregator function
Aggregator = Callable[[str], PortfolioMetrics]

# flake8: noqa: E501


class SnapshotAggregationService:
    """Service responsible for building and saving portfolio snapshots."""

    def __init__(
        self,
        db_session: Session | AsyncSession,
        aggregator: Aggregator = aggregate_portfolio_metrics,
    ) -> None:
        self.db_session = db_session
        self.aggregator = aggregator

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    async def build_snapshot(self, user_address: str) -> PortfolioSnapshot:
        """Aggregate user metrics and return PortfolioSnapshot (not committed)."""
        metrics = await self.aggregator(user_address)
        return self._metrics_to_snapshot(metrics)

    async def save_snapshot(self, user_address: str) -> PortfolioSnapshot:
        """Aggregate metrics, build snapshot, and persist using *async* session."""
        if not isinstance(self.db_session, AsyncSession):
            raise TypeError("save_snapshot requires an AsyncSession")

        snapshot = await self.build_snapshot(user_address)
        self.db_session.add(snapshot)
        await self.db_session.commit()
        await self.db_session.refresh(snapshot)
        return snapshot

    # ----------------------- Sync helpers (Celery) -----------------------
    def save_snapshot_sync(self, user_address: str) -> PortfolioSnapshot:
        """Sync helper for Celery tasks using a synchronous Session."""
        if isinstance(self.db_session, AsyncSession):
            raise TypeError("save_snapshot_sync requires a sync Session")

        # Support both async and sync aggregator implementations for easier
        # testing / dependency injection.  If the provided aggregator is an
        # async function we need to run it in a private event loop, otherwise
        # we can call it directly.
        if asyncio.iscoroutinefunction(self.aggregator):
            metrics = asyncio.run(self.aggregator(user_address))
        else:
            metrics = self.aggregator(user_address)
        snapshot = self._metrics_to_snapshot(metrics)
        self.db_session.add(snapshot)
        self.db_session.commit()
        return snapshot

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _metrics_to_snapshot(metrics) -> PortfolioSnapshot:  # type: ignore
        """Convert PortfolioMetrics (domain) to PortfolioSnapshot (ORM)."""
        return PortfolioSnapshot(
            user_address=metrics.user_address,
            timestamp=int(metrics.timestamp.timestamp()),
            total_collateral=metrics.total_collateral,
            total_borrowings=metrics.total_borrowings,
            total_collateral_usd=metrics.total_collateral_usd,
            total_borrowings_usd=metrics.total_borrowings_usd,
            aggregate_health_score=metrics.aggregate_health_score,
            aggregate_apy=metrics.aggregate_apy,
            collaterals=[c.model_dump() for c in metrics.collaterals],
            borrowings=[b.model_dump() for b in metrics.borrowings],
            staked_positions=[
                s.model_dump() for s in metrics.staked_positions
            ],
            health_scores=[h.model_dump() for h in metrics.health_scores],
            protocol_breakdown={
                k: v.model_dump()
                for k, v in metrics.protocol_breakdown.items()
            },
        )
