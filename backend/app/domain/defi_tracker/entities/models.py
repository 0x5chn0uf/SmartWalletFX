"""Domain entities for the DeFi Tracker.

These entities are *pure Python* and do **not** depend on SQLAlchemy or
any other infrastructure libraries. Persistence mappings live in the
infrastructure layer (`app.repositories`).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass(slots=True)
class Position:
    """A single DeFi position on a protocol (supply/borrow/staked)."""

    protocol: str
    asset: str
    amount: float
    usd_value: float
    apy: Optional[float] = None  # Some positions have a yield component


@dataclass(slots=True)
class AggregateMetrics:
    """Aggregated metrics for a wallet across protocols at a point in time."""

    id: UUID
    wallet_id: str  # EVM address
    tvl: float
    total_borrowings: float
    aggregate_apy: Optional[float]
    as_of: datetime
    positions: List[Position]

    @classmethod
    def new(
        cls, wallet_id: str, *, as_of: Optional[datetime] = None
    ) -> "AggregateMetrics":
        return cls(
            id=uuid4(),
            wallet_id=wallet_id,
            tvl=0.0,
            total_borrowings=0.0,
            aggregate_apy=None,
            as_of=as_of or datetime.utcnow(),
            positions=[],
        )
