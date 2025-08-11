from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.schemas.historical_balance import HistoricalBalanceCreate
from app.models.historical_balance import HistoricalBalance


class HistoricalBalanceRepositoryInterface(ABC):
    """Interface for historical token balance persistence."""

    @abstractmethod
    async def create(
        self, data: HistoricalBalanceCreate
    ) -> HistoricalBalance:  # pragma: no cover
        """Create a new historical balance record."""
