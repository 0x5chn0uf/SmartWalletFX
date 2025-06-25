from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from . import Base


class AggregateMetricsModel(Base):
    """SQLAlchemy model for DeFi aggregate metrics with business logic."""

    __tablename__ = "aggregate_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    wallet_id = Column(String(64), index=True, nullable=False)
    as_of = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    tvl = Column(Float, nullable=False, default=0.0)
    total_borrowings = Column(Float, nullable=False, default=0.0)
    aggregate_apy = Column(Float, nullable=True)
    positions = Column(JSON, nullable=False, default=list)

    def __repr__(self):
        """Return a string representation of the aggregate metrics instance."""
        return f"<AggregateMetricsModel wallet_id={self.wallet_id} tvl={self.tvl}>"

    def calculate_weighted_apy(self) -> Optional[float]:
        """Calculate weighted average APY across all positions."""
        if not self.positions:
            return None

        total_value = sum(pos.get("usd_value", 0) for pos in self.positions)
        if total_value == 0:
            return None

        weighted_sum = sum(
            pos.get("apy", 0) * pos.get("usd_value", 0)
            for pos in self.positions
            if pos.get("apy") and pos.get("usd_value")
        )
        return weighted_sum / total_value if total_value > 0 else None

    def update_aggregate_apy(self) -> None:
        """Update the aggregate APY based on current positions."""
        self.aggregate_apy = self.calculate_weighted_apy()

    def add_position(
        self,
        protocol: str,
        asset: str,
        amount: float,
        usd_value: float,
        apy: Optional[float] = None,
    ) -> None:
        """Add a new position to the aggregate metrics."""
        position = {
            "protocol": protocol,
            "asset": asset,
            "amount": amount,
            "usd_value": usd_value,
            "apy": apy,
        }
        self.positions.append(position)
        self.tvl += usd_value
        self.update_aggregate_apy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "wallet_id": self.wallet_id,
            "as_of": self.as_of.isoformat() if self.as_of else None,
            "tvl": self.tvl,
            "total_borrowings": self.total_borrowings,
            "aggregate_apy": self.aggregate_apy,
            "positions": self.positions,
        }

    @classmethod
    def create_new(cls, wallet_id: str) -> "AggregateMetricsModel":
        """Factory method for creating new aggregate metrics instance."""
        return cls(
            wallet_id=wallet_id.lower(),
            tvl=0.0,
            total_borrowings=0.0,
            positions=[],
            as_of=datetime.utcnow(),
        )
