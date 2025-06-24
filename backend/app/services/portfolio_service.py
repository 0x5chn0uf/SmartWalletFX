"""
Portfolio calculation and analysis service.

This service provides comprehensive portfolio analysis including:
- Performance metrics calculation
- Historical data analysis
- Portfolio risk assessment
- Return calculations
- Asset allocation analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Union

from app.repositories.portfolio_snapshot_repository import (
    PortfolioSnapshotRepository,
)
from app.schemas.defi import PortfolioSnapshot as DefiPortfolioSnapshot
from app.schemas.portfolio_metrics import PortfolioMetrics
from app.schemas.portfolio_timeline import PortfolioTimeline

_Number = Union[int, float]
logger = logging.getLogger(__name__)


class PortfolioCalculationService:
    """Service for calculating portfolio metrics and analytics."""

    def __init__(self, db):
        self.db = db
        self.snapshot_repo = PortfolioSnapshotRepository(db)

    # ------------------------------------------------------------------
    # Public helpers used in tests
    # ------------------------------------------------------------------
    async def calculate_portfolio_metrics(self, user_address: str) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics."""
        try:
            snapshot = await self._get_latest_snapshot(user_address)
            if not snapshot:
                return self._empty_metrics(user_address)

            # Use helper function for safe attribute access
            def _get(obj, key, default=0.0):
                if hasattr(obj, key):
                    return getattr(obj, key, default)
                elif isinstance(obj, dict):
                    return obj.get(key, default)
                return default

            total_collateral = sum(_get(c, "amount") for c in snapshot.collaterals)
            total_borrowings = sum(_get(b, "amount") for b in snapshot.borrowings)
            total_collateral_usd = sum(
                _get(c, "usd_value") for c in snapshot.collaterals
            )
            total_borrowings_usd = sum(
                _get(b, "usd_value") for b in snapshot.borrowings
            )

            aggregate_apy = self._aggregate_apy(snapshot.staked_positions)

            return PortfolioMetrics(
                user_address=user_address,
                total_collateral=total_collateral,
                total_borrowings=total_borrowings,
                total_collateral_usd=total_collateral_usd,
                total_borrowings_usd=total_borrowings_usd,
                aggregate_apy=aggregate_apy,
                collaterals=snapshot.collaterals,
                borrowings=snapshot.borrowings,
                staked_positions=snapshot.staked_positions,
                health_scores=snapshot.health_scores,
            )
        except Exception:
            # Return empty metrics on any error
            return self._empty_metrics(user_address)

    async def calculate_portfolio_timeline(
        self,
        user_address: str,
        limit: int = 30,
        offset: int = 0,
        interval: str = "daily",
    ) -> PortfolioTimeline:
        """Calculate portfolio timeline data."""
        try:
            # Get historical snapshots from the last 30 days
            end_ts = int(datetime.utcnow().timestamp())
            start_ts = int((datetime.utcnow() - timedelta(days=30)).timestamp())

            snapshots = await self.snapshot_repo.get_snapshots_by_address_and_range(
                user_address=user_address,
                from_ts=start_ts,
                to_ts=end_ts,
                limit=limit,
                offset=offset,
            )

            return PortfolioTimeline(
                timestamps=[s.timestamp for s in snapshots],
                collateral_usd=[s.total_collateral_usd for s in snapshots],
                borrowings_usd=[s.total_borrowings_usd for s in snapshots],
            )
        except Exception:
            # Return empty timeline on any error
            return PortfolioTimeline(
                timestamps=[],
                collateral_usd=[],
                borrowings_usd=[],
            )

    def calculate_performance_metrics(
        self, user_address: str, period_days: int = 30
    ) -> Dict[str, float]:
        end = datetime.utcnow()
        start = end - timedelta(days=period_days)
        start_snap = self._get_snapshot_at_timestamp(user_address, start)
        end_snap = self._get_snapshot_at_timestamp(user_address, end)
        if not start_snap or not end_snap:
            return self._empty_performance()
        total_return = self._total_return(start_snap, end_snap)
        max_dd = self._max_drawdown(user_address, start, end)
        return {
            "total_return": total_return,
            "max_drawdown": max_dd,
        }

    async def calculate_risk_metrics(self, user_address: str) -> Dict[str, float]:
        """Calculate risk metrics for a user's portfolio."""
        snapshot = await self._get_latest_snapshot(user_address)
        if not snapshot:
            return {
                "collateralization_ratio": 0.0,
                "utilization_rate": 0.0,
                "concentration_risk": 0.0,
            }

        # Calculate totals from collaterals and borrowings
        total_collateral = sum(
            getattr(c, "usd_value", 0.0) for c in snapshot.collaterals
        )
        total_borrowings = sum(
            getattr(b, "usd_value", 0.0) for b in snapshot.borrowings
        )

        # Risk metrics
        collateralization_ratio = (
            total_collateral / total_borrowings if total_borrowings > 0 else 0.0
        )
        utilization_rate = (
            total_borrowings / total_collateral if total_collateral > 0 else 0.0
        )

        # Concentration risk (simplified - could be enhanced)
        concentration_risk = 0.0
        if total_collateral > 0:
            max_position = max(
                (getattr(c, "usd_value", 0.0) for c in snapshot.collaterals),
                default=0.0,
            )
            concentration_risk = max_position / total_collateral

        return {
            "collateralization_ratio": collateralization_ratio,
            "utilization_rate": utilization_rate,
            "concentration_risk": concentration_risk,
        }

    # ------------------------------------------------------------------
    # Internal calculations
    # ------------------------------------------------------------------
    @staticmethod
    def _aggregate_apy(positions: Sequence[Dict[str, _Number]]) -> Optional[float]:
        if not positions:
            return None

        def _get(item, key, default=0.0):
            return (
                item.get(key, default)
                if isinstance(item, dict)
                else getattr(item, key, default)
            )

        total = sum(_get(p, "usd_value", 0.0) for p in positions)
        if total == 0:
            return None
        weighted = sum(
            _get(p, "apy", 0.0) * _get(p, "usd_value", 0.0) for p in positions
        )
        return round(weighted / total, 4)

    @staticmethod
    def _total_return(
        start: DefiPortfolioSnapshot, end: DefiPortfolioSnapshot
    ) -> float:
        start_val = start.total_collateral_usd - start.total_borrowings_usd
        end_val = end.total_collateral_usd - end.total_borrowings_usd
        return (end_val - start_val) / start_val if start_val > 0 else 0.0

    def _max_drawdown(self, user: str, start: datetime, end: datetime) -> float:
        vals: List[float] = []
        cur = start
        while cur <= end:
            snap = self._get_snapshot_at_timestamp(user, cur)
            if snap is not None:
                vals.append(snap.total_collateral_usd - snap.total_borrowings_usd)
            cur += timedelta(days=1)
        if not vals:
            return 0.0
        peak = vals[0]
        max_dd = 0.0
        for v in vals:
            if v > peak:
                peak = v
            if peak:
                max_dd = max(max_dd, (peak - v) / peak)
        return max_dd

    @staticmethod
    def _calculate_aggregate_apy(
        positions: Sequence[Dict[str, _Number]]
    ) -> Optional[float]:
        return PortfolioCalculationService._aggregate_apy(positions)

    @staticmethod
    def _calculate_total_return(
        start: DefiPortfolioSnapshot, end: DefiPortfolioSnapshot
    ) -> float:
        return PortfolioCalculationService._total_return(start, end)

    # ------------------------------------------------------------------
    # Empty placeholders
    # ------------------------------------------------------------------
    @staticmethod
    def _empty_metrics(user: str) -> PortfolioMetrics:
        return PortfolioMetrics(
            user_address=user,
            total_collateral=0.0,
            total_borrowings=0.0,
            total_collateral_usd=0.0,
            total_borrowings_usd=0.0,
            aggregate_health_score=None,
            aggregate_apy=None,
            collaterals=[],
            borrowings=[],
            staked_positions=[],
            health_scores=[],
            protocol_breakdown={},
            timestamp=datetime.utcnow(),
        )

    @staticmethod
    def _empty_performance() -> Dict[str, float]:
        return {
            "total_return": 0.0,
            "max_drawdown": 0.0,
        }

    async def _get_latest_snapshot(self, user_address: str):
        """Get the latest portfolio snapshot for a user."""
        return await self.snapshot_repo.get_latest_snapshot_by_address(user_address)
