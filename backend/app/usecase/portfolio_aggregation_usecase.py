import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.schemas.defi import Borrowing, Collateral, HealthScore, StakedPosition
from app.usecase.defi_aave_usecase import get_aave_user_snapshot_usecase
from app.usecase.defi_compound_usecase import (
    get_compound_user_snapshot_usecase,
)
from app.usecase.defi_radiant_usecase import get_radiant_user_snapshot_usecase


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


async def aggregate_portfolio_metrics(address: str) -> PortfolioMetrics:
    # Fetch all protocol snapshots concurrently
    snapshots = await asyncio.gather(
        get_aave_user_snapshot_usecase(address),
        get_compound_user_snapshot_usecase(address),
        get_radiant_user_snapshot_usecase(address),
    )
    protocol_names = ["aave", "compound", "radiant"]
    collaterals = []
    borrowings = []
    staked_positions = []
    health_scores = []
    protocol_breakdown = {}
    total_collateral_usd = 0.0
    total_borrowings_usd = 0.0
    for snap, proto in zip(snapshots, protocol_names):
        if snap is None:
            protocol_breakdown[proto] = ProtocolBreakdown(
                protocol=proto,
                total_collateral=0.0,
                total_borrowings=0.0,
                aggregate_health_score=None,
                aggregate_apy=None,
                collaterals=[],
                borrowings=[],
                staked_positions=[],
                health_scores=[],
            )
            continue
        proto_collateral = sum(c.amount for c in snap.collaterals)
        proto_borrowings = sum(b.amount for b in snap.borrowings)
        proto_health = (
            sum(h.score for h in snap.health_scores) / len(snap.health_scores)
            if snap.health_scores
            else None
        )
        proto_staked = sum(s.amount for s in snap.staked_positions)
        proto_apy = (
            sum((s.apy or 0) * s.amount for s in snap.staked_positions)
            / proto_staked
            if proto_staked > 0
            else None
        )
        protocol_breakdown[proto] = ProtocolBreakdown(
            protocol=proto,
            total_collateral=proto_collateral,
            total_borrowings=proto_borrowings,
            aggregate_health_score=proto_health,
            aggregate_apy=proto_apy,
            collaterals=snap.collaterals,
            borrowings=snap.borrowings,
            staked_positions=snap.staked_positions,
            health_scores=snap.health_scores,
        )
        collaterals.extend(snap.collaterals)
        borrowings.extend(snap.borrowings)
        staked_positions.extend(snap.staked_positions)
        health_scores.extend(snap.health_scores)
        # USD conversion (dummy)
        total_collateral_usd += sum(
            to_usd(c.amount, getattr(c, "symbol", "USD"))
            for c in snap.collaterals
        )
        total_borrowings_usd += sum(
            to_usd(b.amount, getattr(b, "symbol", "USD"))
            for b in snap.borrowings
        )
    total_collateral = sum(c.amount for c in collaterals)
    total_borrowings = sum(b.amount for b in borrowings)
    aggregate_health_score = (
        sum(h.score for h in health_scores) / len(health_scores)
        if health_scores
        else None
    )
    total_staked = sum(s.amount for s in staked_positions)
    aggregate_apy = (
        sum((s.apy or 0) * s.amount for s in staked_positions) / total_staked
        if total_staked > 0
        else None
    )
    # Historical snapshots: placeholder (None for now)
    historical_snapshots = None
    return PortfolioMetrics(
        user_address=address,
        total_collateral=total_collateral,
        total_borrowings=total_borrowings,
        total_collateral_usd=total_collateral_usd,
        total_borrowings_usd=total_borrowings_usd,
        aggregate_health_score=aggregate_health_score,
        aggregate_apy=aggregate_apy,
        collaterals=collaterals,
        borrowings=borrowings,
        staked_positions=staked_positions,
        health_scores=health_scores,
        protocol_breakdown=protocol_breakdown,
        historical_snapshots=historical_snapshots,
        timestamp=datetime.utcnow(),
    )
