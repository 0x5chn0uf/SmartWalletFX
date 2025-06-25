from __future__ import annotations

from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.aggregate_metrics import AggregateMetricsModel


class AggregateMetricsRepository:
    """Asynchronous repository for CRUD operations on AggregateMetricsModel."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # ---------------------------------------------------------------------
    # Query helpers
    # ---------------------------------------------------------------------

    async def get_latest(self, wallet_id: str) -> Optional[AggregateMetricsModel]:
        """Get the latest aggregate metrics for a wallet."""
        stmt = (
            select(AggregateMetricsModel)
            .filter(AggregateMetricsModel.wallet_id == wallet_id.lower())
            .order_by(desc(AggregateMetricsModel.as_of))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(
        self, wallet_id: str, limit: int = 100, offset: int = 0
    ) -> List[AggregateMetricsModel]:
        """Get historical aggregate metrics for a wallet."""
        stmt = (
            select(AggregateMetricsModel)
            .filter(AggregateMetricsModel.wallet_id == wallet_id.lower())
            .order_by(desc(AggregateMetricsModel.as_of))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def exists(self, wallet_id: str) -> bool:
        """Return True if aggregate metrics exist for the given wallet."""
        stmt = (
            select(AggregateMetricsModel.id)
            .filter(AggregateMetricsModel.wallet_id == wallet_id.lower())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    # ---------------------------------------------------------------------
    # Persistence helpers
    # ---------------------------------------------------------------------

    async def save(self, metrics: AggregateMetricsModel) -> AggregateMetricsModel:
        """Persist metrics instance and commit the transaction."""
        self._session.add(metrics)
        await self._session.commit()
        await self._session.refresh(metrics)
        return metrics

    async def upsert(self, metrics: AggregateMetricsModel) -> AggregateMetricsModel:
        """Insert or update aggregate metrics for a wallet."""
        # Check if metrics exist for this wallet
        existing = await self.get_latest(metrics.wallet_id)
        if existing:
            # Update existing record
            existing.tvl = metrics.tvl
            existing.total_borrowings = metrics.total_borrowings
            existing.aggregate_apy = metrics.aggregate_apy
            existing.positions = metrics.positions
            existing.as_of = metrics.as_of
            await self._session.commit()
            await self._session.refresh(existing)
            return existing
        else:
            # Create new record
            return await self.save(metrics)

    async def delete_by_wallet_id(self, wallet_id: str) -> None:
        """Delete all aggregate metrics for a wallet."""
        stmt = select(AggregateMetricsModel).filter(
            AggregateMetricsModel.wallet_id == wallet_id.lower()
        )
        result = await self._session.execute(stmt)
        metrics_list = result.scalars().all()

        for metrics in metrics_list:
            await self._session.delete(metrics)

        await self._session.commit()
