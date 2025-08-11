from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.portfolio_snapshot import PortfolioSnapshot


class PortfolioSnapshotRepositoryInterface(ABC):
    """Interface for portfolio snapshot persistence and caching."""

    @abstractmethod
    async def create_snapshot(
        self, snapshot: PortfolioSnapshot
    ) -> PortfolioSnapshot:  # pragma: no cover
        """Persist a new snapshot."""

    @abstractmethod
    async def get_snapshots_by_address_and_range(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PortfolioSnapshot]:  # pragma: no cover
        """Retrieve snapshots for an address within a timestamp range."""

    @abstractmethod
    async def get_latest_snapshot_by_address(
        self, user_address: str
    ) -> Optional[PortfolioSnapshot]:  # pragma: no cover
        """Return the most recent snapshot for a wallet address."""

    @abstractmethod
    async def get_by_wallet_address(
        self, wallet_address: str
    ) -> List[PortfolioSnapshot]:  # pragma: no cover
        """Return snapshots for a specific wallet address."""

    @abstractmethod
    async def delete_snapshot(self, snapshot_id: int) -> None:  # pragma: no cover
        """Delete a snapshot by id."""

    @abstractmethod
    async def get_cache(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        interval: str,
        limit: int,
        offset: int,
    ) -> str | None:  # pragma: no cover
        """Retrieve cached JSON response if available."""

    @abstractmethod
    async def set_cache(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        interval: str,
        limit: int,
        offset: int,
        response_json: str,
        expires_in_seconds: int = 3600,
    ) -> None:  # pragma: no cover
        """Persist cached response."""

    @abstractmethod
    async def get_timeline(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        limit: int = 100,
        offset: int = 0,
        interval: str = "none",
    ) -> List[PortfolioSnapshot]:  # pragma: no cover
        """Return timeline of snapshots with optional interval aggregation."""
