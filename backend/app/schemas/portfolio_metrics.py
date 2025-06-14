from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.schemas.defi import Borrowing, Collateral, HealthScore, StakedPosition


# Placeholder for USD conversion (to be replaced with real price oracle)
def to_usd(amount: float, symbol: str) -> float:
    # TODO: Integrate with price oracle
    return amount  # 1:1 for now


class ProtocolBreakdown(BaseModel):
    protocol: str
    total_collateral: float
    total_borrowings: float
    aggregate_health_score: Optional[float]
    aggregate_apy: Optional[float]
    collaterals: List[Collateral]
    borrowings: List[Borrowing]
    staked_positions: List[StakedPosition]
    health_scores: List[HealthScore]


class PortfolioMetrics(BaseModel):
    user_address: str
    total_collateral: float
    total_borrowings: float
    total_collateral_usd: float
    total_borrowings_usd: float
    aggregate_health_score: Optional[float]
    aggregate_apy: Optional[float]
    collaterals: List[Collateral]
    borrowings: List[Borrowing]
    staked_positions: List[StakedPosition]
    health_scores: List[HealthScore]
    protocol_breakdown: Dict[str, ProtocolBreakdown]
    historical_snapshots: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime
