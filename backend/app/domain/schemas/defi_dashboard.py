from datetime import datetime
from typing import List

from pydantic import BaseModel


class ProtocolBreakdown(BaseModel):
    name: str
    tvl: float
    apy: float
    positions: int


class DefiKPI(BaseModel):
    tvl: float
    apy: float
    protocols: List[ProtocolBreakdown]
    updated_at: datetime
