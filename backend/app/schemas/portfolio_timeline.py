from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.schemas.defi import PortfolioSnapshot


class TimelineResponse(BaseModel):
    """Structured response for /defi/timeline endpoint."""

    snapshots: List[PortfolioSnapshot]
    interval: str  # none, daily, weekly
    limit: int
    offset: int
    total: int

    class Config:
        from_attributes = True


class PortfolioSnapshotResponse(BaseModel):
    user_address: str
    timestamp: datetime
    total_collateral_usd: float
    total_borrowings_usd: float

    class Config:
        from_attributes = True


class PortfolioTimeline(BaseModel):
    timestamps: list[int]
    collateral_usd: list[float]
    borrowings_usd: list[float]
