from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.schemas.defi_aggregate import (
    AggregateMetricsSchema as AggregateMetrics,
)


class AggregateMetricsRepositoryInterface(ABC):
    """Port for persisting and retrieving aggregated metrics."""

    @abstractmethod
    async def upsert(self, metrics: AggregateMetrics) -> None:  # pragma: no cover
        """Create or update aggregate metrics in the persistence store."""

    @abstractmethod
    async def get_latest(
        self, wallet_id: str
    ) -> Optional[AggregateMetrics]:  # pragma: no cover
        """Return the most recent metrics for the given wallet, or None."""

    @abstractmethod
    async def get_history(
        self, wallet_id: str, limit: int = 100, offset: int = 0
    ) -> List[AggregateMetrics]:  # pragma: no cover
        """Return historical metrics for a wallet (descending order)."""
