from __future__ import annotations

"""Aggregator that converts individual protocol snapshots into unified metrics.

This module mirrors the logic in :pymod:`app.usecase.portfolio_aggregation_usecase`
 but works with a *dynamic* list of :class:`ProtocolAdapter` instances instead of
 hard-coding the protocols.  This will allow new adapters to be registered
 without modifying the aggregator.
"""

import asyncio
from datetime import datetime
from typing import List, Optional

from app.adapters.protocols.base import ProtocolAdapter
from app.schemas.defi import (
    Borrowing,
    Collateral,
    HealthScore,
    StakedPosition,
)
from app.schemas.portfolio_metrics import (
    PortfolioMetrics,
    ProtocolBreakdown,
    to_usd,
)

__all__ = ["aggregate_portfolio_metrics_from_adapters"]


async def aggregate_portfolio_metrics_from_adapters(
    address: str, adapters: List[ProtocolAdapter]
) -> PortfolioMetrics:
    """Aggregate portfolio data for *address* using the supplied *adapters*."""

    # Fetch all snapshots concurrently
    snapshot_coros = [adapter.fetch_snapshot(address) for adapter in adapters]
    snapshots = await asyncio.gather(*snapshot_coros)

    collaterals: list[Collateral] = []
    borrowings: list[Borrowing] = []
    staked_positions: list[StakedPosition] = []
    health_scores: list[HealthScore] = []
    protocol_breakdown: dict[str, ProtocolBreakdown] = {}
    total_collateral_usd = 0.0
    total_borrowings_usd = 0.0

    for adapter, snap in zip(adapters, snapshots):
        proto = adapter.name
        if snap is None:
            # Empty placeholder to keep downstream UI consistent
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
        proto_health: Optional[float] = (
            sum(h.score for h in snap.health_scores) / len(snap.health_scores)
            if snap.health_scores
            else None
        )
        proto_staked = sum(s.amount for s in snap.staked_positions)
        proto_apy: Optional[float] = (
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

        # USD conversion (placeholder logic)
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
    aggregate_health_score: Optional[float] = (
        sum(h.score for h in health_scores) / len(health_scores)
        if health_scores
        else None
    )
    total_staked = sum(s.amount for s in staked_positions)
    aggregate_apy: Optional[float] = (
        sum((s.apy or 0) * s.amount for s in staked_positions)
        / total_staked
        if total_staked > 0
        else None
    )

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
        historical_snapshots=None,
        timestamp=datetime.utcnow(),
    )