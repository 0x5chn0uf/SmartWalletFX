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
        orm_mode = True 