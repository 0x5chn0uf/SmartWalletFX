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
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.schemas.defi import PortfolioSnapshot as DefiPortfolioSnapshot
from app.schemas.portfolio_metrics import PortfolioMetrics, ProtocolBreakdown
from app.schemas.portfolio_timeline import PortfolioTimeline

logger = logging.getLogger(__name__)


class PortfolioCalculationService:
    """Service for calculating portfolio metrics and performing data analysis."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def calculate_portfolio_metrics(
        self, user_address: str, timestamp: Optional[datetime] = None
    ) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio metrics for a user.

        Args:
            user_address: The user's wallet address
            timestamp: Optional timestamp for historical metrics

        Returns:
            PortfolioMetrics object with calculated metrics
        """
        try:
            # Get the latest snapshot
            snapshot = (
                self._get_snapshot_at_timestamp(user_address, timestamp)
                if timestamp
                else self._get_latest_snapshot(user_address)
            )

            if not snapshot:
                return self._create_empty_metrics(user_address)

            # Ensure we can safely access data regardless of model/dict types
            collaterals_dict = [self._to_dict(c) for c in snapshot.collaterals]
            borrowings_dict = [self._to_dict(b) for b in snapshot.borrowings]
            staked_positions_dict = [
                self._to_dict(p) for p in snapshot.staked_positions
            ]
            health_scores_dict = [self._to_dict(h) for h in snapshot.health_scores]

            # Calculate totals
            total_collateral = sum(c["amount"] for c in collaterals_dict)
            total_borrowings = sum(b["amount"] for b in borrowings_dict)
            total_collateral_usd = sum(c["usd_value"] for c in collaterals_dict)
            total_borrowings_usd = sum(b["usd_value"] for b in borrowings_dict)

            # Calculate aggregate health score (weighted average)
            aggregate_health_score = self._calculate_aggregate_health_score(
                health_scores_dict
            )

            # Calculate aggregate APY
            aggregate_apy = self._calculate_aggregate_apy(staked_positions_dict)

            # Create protocol breakdown
            protocol_breakdown = self._create_protocol_breakdown(
                collaterals_dict,
                borrowings_dict,
                staked_positions_dict,
                health_scores_dict,
            )

            return PortfolioMetrics(
                user_address=user_address,
                total_collateral=total_collateral,
                total_borrowings=total_borrowings,
                total_collateral_usd=total_collateral_usd,
                total_borrowings_usd=total_borrowings_usd,
                aggregate_health_score=aggregate_health_score,
                aggregate_apy=aggregate_apy,
                collaterals=collaterals_dict,
                borrowings=borrowings_dict,
                staked_positions=staked_positions_dict,
                health_scores=health_scores_dict,
                protocol_breakdown=protocol_breakdown,
                timestamp=datetime.fromtimestamp(snapshot.timestamp),
            )

        except Exception as e:
            logger.error(f"Error calculating portfolio metrics for {user_address}: {e}")
            return self._create_empty_metrics(user_address)

    def calculate_portfolio_timeline(
        self,
        user_address: str,
        interval: str = "daily",
        limit: int = 30,
        offset: int = 0,
    ) -> PortfolioTimeline:
        """
        Calculate portfolio timeline data for visualization.

        Args:
            user_address: The user's wallet address
            interval: Data interval (daily, weekly, monthly)
            limit: Number of data points to return
            offset: Offset for pagination

        Returns:
            PortfolioTimeline object with time series data
        """
        try:
            # Get historical snapshots
            snapshots = self._get_historical_snapshots(
                user_address, interval, limit, offset
            )

            timestamps = []
            collateral_usd = []
            borrowings_usd = []

            # Ensure chronological order (oldest first) so the data series is intuitive
            for snapshot in reversed(snapshots):
                timestamps.append(snapshot.timestamp)
                collateral_usd.append(snapshot.total_collateral_usd)
                borrowings_usd.append(snapshot.total_borrowings_usd)

            return PortfolioTimeline(
                timestamps=timestamps,
                collateral_usd=collateral_usd,
                borrowings_usd=borrowings_usd,
            )

        except Exception as e:
            logger.error(
                f"Error calculating portfolio timeline for {user_address}: {e}"
            )
            return PortfolioTimeline(
                timestamps=[], collateral_usd=[], borrowings_usd=[]
            )

    def calculate_performance_metrics(
        self, user_address: str, period_days: int = 30
    ) -> Dict[str, float]:
        """
        Calculate performance metrics for a given period.

        Args:
            user_address: The user's wallet address
            period_days: Number of days to analyze

        Returns:
            Dictionary with performance metrics
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)

            # Get snapshots for the period
            start_snapshot = self._get_snapshot_at_timestamp(user_address, start_date)
            end_snapshot = self._get_snapshot_at_timestamp(user_address, end_date)

            if not start_snapshot or not end_snapshot:
                return self._create_empty_performance_metrics()

            # Calculate metrics
            total_return = self._calculate_total_return(start_snapshot, end_snapshot)
            volatility = self._calculate_volatility(user_address, start_date, end_date)
            sharpe_ratio = self._calculate_sharpe_ratio(total_return, volatility)
            try:
                max_drawdown = self._calculate_max_drawdown(
                    user_address, start_date, end_date
                )
            except Exception:
                max_drawdown = 0.0

            return {
                "total_return": total_return,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "period_days": period_days,
            }

        except Exception as e:
            logger.error(
                f"Error calculating performance metrics for {user_address}: {e}"
            )
            return self._create_empty_performance_metrics()

    def calculate_risk_metrics(self, user_address: str) -> Dict[str, float]:
        """
        Calculate risk metrics for the portfolio.

        Args:
            user_address: The user's wallet address

        Returns:
            Dictionary with risk metrics
        """
        try:
            # Get current portfolio metrics
            metrics = self.calculate_portfolio_metrics(user_address)

            # Calculate risk metrics
            collateralization_ratio = (
                metrics.total_collateral_usd / metrics.total_borrowings_usd
                if metrics.total_borrowings_usd > 0
                else float("inf")
            )

            utilization_rate = (
                metrics.total_borrowings_usd / metrics.total_collateral_usd
                if metrics.total_collateral_usd > 0
                else 0.0
            )

            # Calculate diversification score
            diversification_score = self._calculate_diversification_score(metrics)

            # Calculate concentration risk
            concentration_risk = self._calculate_concentration_risk(metrics)

            return {
                "collateralization_ratio": collateralization_ratio,
                "utilization_rate": utilization_rate,
                "diversification_score": diversification_score,
                "concentration_risk": concentration_risk,
                "aggregate_health_score": metrics.aggregate_health_score or 0.0,
            }

        except Exception as e:
            logger.error(f"Error calculating risk metrics for {user_address}: {e}")
            return self._create_empty_risk_metrics()

    def _get_latest_snapshot(
        self, user_address: str
    ) -> Optional[DefiPortfolioSnapshot]:
        """Get the latest portfolio snapshot for a user."""
        snapshot = (
            self.db.query(PortfolioSnapshot)
            .filter(PortfolioSnapshot.user_address == user_address)
            .order_by(PortfolioSnapshot.timestamp.desc())
            .first()
        )

        if not snapshot:
            return None

        return self._convert_db_snapshot_to_schema(snapshot)

    def _get_snapshot_at_timestamp(
        self, user_address: str, timestamp: datetime
    ) -> Optional[DefiPortfolioSnapshot]:
        """Get portfolio snapshot closest to the given timestamp."""
        target_timestamp = int(timestamp.timestamp())

        snapshot = (
            self.db.query(PortfolioSnapshot)
            .filter(PortfolioSnapshot.user_address == user_address)
            .filter(PortfolioSnapshot.timestamp <= target_timestamp)
            .order_by(PortfolioSnapshot.timestamp.desc())
            .first()
        )

        if not snapshot:
            return None

        return self._convert_db_snapshot_to_schema(snapshot)

    def _get_historical_snapshots(
        self, user_address: str, interval: str, limit: int, offset: int
    ) -> List[PortfolioSnapshot]:
        """Get historical snapshots with pagination."""
        query = (
            self.db.query(PortfolioSnapshot)
            .filter(PortfolioSnapshot.user_address == user_address)
            .order_by(PortfolioSnapshot.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )

        return query.all()

    def _convert_db_snapshot_to_schema(
        self, db_snapshot: PortfolioSnapshot
    ) -> DefiPortfolioSnapshot:
        """Convert database snapshot to schema object."""
        return DefiPortfolioSnapshot(
            user_address=db_snapshot.user_address,
            timestamp=db_snapshot.timestamp,
            total_collateral=db_snapshot.total_collateral,
            total_borrowings=db_snapshot.total_borrowings,
            total_collateral_usd=db_snapshot.total_collateral_usd,
            total_borrowings_usd=db_snapshot.total_borrowings_usd,
            aggregate_health_score=db_snapshot.aggregate_health_score,
            aggregate_apy=db_snapshot.aggregate_apy,
            collaterals=db_snapshot.collaterals,
            borrowings=db_snapshot.borrowings,
            staked_positions=db_snapshot.staked_positions,
            health_scores=db_snapshot.health_scores,
            protocol_breakdown=db_snapshot.protocol_breakdown,
        )

    def _calculate_aggregate_health_score(
        self, health_scores: List[Dict]
    ) -> Optional[float]:
        """Calculate weighted average health score."""
        if not health_scores:
            return None

        total_weight = 0
        weighted_sum = 0

        for health_score in health_scores:
            # Use protocol's total value as weight
            weight = health_score.get("total_value", 1.0)
            score = health_score.get("score", 0.0)

            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else None

    def _calculate_aggregate_apy(self, staked_positions: List[Dict]) -> Optional[float]:
        """Calculate weighted average APY."""
        if not staked_positions:
            return None

        total_value = 0
        weighted_sum = 0

        for position in staked_positions:
            value = position.get("usd_value", 0.0)
            apy = position.get("apy", 0.0)

            weighted_sum += apy * value
            total_value += value

        if total_value == 0:
            return None

        return round(weighted_sum / total_value, 3)

    def _create_protocol_breakdown(
        self,
        collaterals: List[Dict],
        borrowings: List[Dict],
        staked_positions: List[Dict],
        health_scores: List[Dict],
    ) -> Dict[str, ProtocolBreakdown]:
        """Create protocol breakdown from snapshot data lists (as dicts)."""
        breakdown: Dict[str, Dict] = {}

        # Group by protocol for collaterals
        for collateral in collaterals:
            protocol = collateral.get("protocol", "OTHER")
            if protocol not in breakdown:
                breakdown[protocol] = {
                    "protocol": protocol,
                    "total_collateral": 0.0,
                    "total_borrowings": 0.0,
                    "aggregate_health_score": None,
                    "aggregate_apy": None,
                    "collaterals": [],
                    "borrowings": [],
                    "staked_positions": [],
                    "health_scores": [],
                }

            breakdown[protocol]["total_collateral"] += collateral.get("amount", 0.0)
            breakdown[protocol]["collaterals"].append(collateral)

        # Add borrowings
        for borrowing in borrowings:
            protocol = borrowing.get("protocol", "OTHER")
            if protocol not in breakdown:
                breakdown[protocol] = {
                    "protocol": protocol,
                    "total_collateral": 0.0,
                    "total_borrowings": 0.0,
                    "aggregate_health_score": None,
                    "aggregate_apy": None,
                    "collaterals": [],
                    "borrowings": [],
                    "staked_positions": [],
                    "health_scores": [],
                }

            breakdown[protocol]["total_borrowings"] += borrowing.get("amount", 0.0)
            breakdown[protocol]["borrowings"].append(borrowing)

        # Add staked positions
        for position in staked_positions:
            protocol = position.get("protocol", "OTHER")
            if protocol not in breakdown:
                breakdown[protocol] = {
                    "protocol": protocol,
                    "total_collateral": 0.0,
                    "total_borrowings": 0.0,
                    "aggregate_health_score": None,
                    "aggregate_apy": None,
                    "collaterals": [],
                    "borrowings": [],
                    "staked_positions": [],
                    "health_scores": [],
                }

            breakdown[protocol]["staked_positions"].append(position)

        # Add health scores
        for health_score in health_scores:
            protocol = health_score.get("protocol", "OTHER")
            if protocol not in breakdown:
                breakdown[protocol] = {
                    "protocol": protocol,
                    "total_collateral": 0.0,
                    "total_borrowings": 0.0,
                    "aggregate_health_score": None,
                    "aggregate_apy": None,
                    "collaterals": [],
                    "borrowings": [],
                    "staked_positions": [],
                    "health_scores": [],
                }

            breakdown[protocol]["health_scores"].append(health_score)

        # Calculate protocol-specific metrics
        for protocol_data in breakdown.values():
            protocol_data[
                "aggregate_health_score"
            ] = self._calculate_aggregate_health_score(protocol_data["health_scores"])
            protocol_data["aggregate_apy"] = self._calculate_aggregate_apy(
                protocol_data["staked_positions"]
            )

        return breakdown

    def _calculate_total_return(
        self, start_snapshot: DefiPortfolioSnapshot, end_snapshot: DefiPortfolioSnapshot
    ) -> float:
        """Calculate total return between two snapshots."""
        start_value = (
            start_snapshot.total_collateral_usd - start_snapshot.total_borrowings_usd
        )
        end_value = (
            end_snapshot.total_collateral_usd - end_snapshot.total_borrowings_usd
        )

        if start_value <= 0:
            return 0.0

        return (end_value - start_value) / start_value

    def _calculate_volatility(
        self, user_address: str, start_date: datetime, end_date: datetime
    ) -> float:
        """Calculate portfolio volatility."""
        # Get daily returns for the period
        daily_returns = []
        current_date = start_date

        while current_date <= end_date:
            snapshot = self._get_snapshot_at_timestamp(user_address, current_date)
            if snapshot:
                daily_returns.append(
                    snapshot.total_collateral_usd - snapshot.total_borrowings_usd
                )
            current_date += timedelta(days=1)

        if len(daily_returns) < 2:
            return 0.0

        # Calculate standard deviation of returns
        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / (
            len(daily_returns) - 1
        )

        return variance**0.5

    def _calculate_sharpe_ratio(self, total_return: float, volatility: float) -> float:
        """Calculate Sharpe ratio (assuming risk-free rate of 0)."""
        if volatility == 0:
            return 0.0

        return total_return / volatility

    def _calculate_max_drawdown(
        self, user_address: str, start_date: datetime, end_date: datetime
    ) -> float:
        """Calculate maximum drawdown."""
        # Get daily portfolio values
        daily_values = []
        current_date = start_date

        while current_date <= end_date:
            snapshot = self._get_snapshot_at_timestamp(user_address, current_date)
            if snapshot:
                daily_values.append(
                    snapshot.total_collateral_usd - snapshot.total_borrowings_usd
                )
            current_date += timedelta(days=1)

        if not daily_values:
            return 0.0

        # Calculate maximum drawdown
        peak = daily_values[0]
        max_drawdown = 0.0

        for value in daily_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak > 0 else 0.0
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_diversification_score(self, metrics: PortfolioMetrics) -> float:
        """Calculate portfolio diversification score (0-1)."""
        if not metrics.collaterals:
            return 0.0

        # Ensure we work with dictionaries
        collaterals = [self._to_dict(c) for c in metrics.collaterals]

        # Calculate Herfindahl-Hirschman Index
        total_value = sum(c.get("usd_value", 0.0) for c in collaterals)
        if total_value == 0:
            return 0.0

        hhi = sum((c.get("usd_value", 0.0) / total_value) ** 2 for c in collaterals)

        # Convert to diversification score (1 - normalized HHI)
        return 1 - (hhi - 1 / len(collaterals)) / (1 - 1 / len(collaterals))

    def _calculate_concentration_risk(self, metrics: PortfolioMetrics) -> float:
        """Calculate concentration risk (0-1)."""
        if not metrics.collaterals:
            return 0.0

        collaterals = [self._to_dict(c) for c in metrics.collaterals]

        # Calculate the percentage of portfolio in the largest position
        total_value = sum(c.get("usd_value", 0.0) for c in collaterals)
        if total_value == 0:
            return 0.0

        max_position = max(c.get("usd_value", 0.0) for c in collaterals)
        return max_position / total_value

    def _create_empty_metrics(self, user_address: str) -> PortfolioMetrics:
        """Create empty portfolio metrics."""
        return PortfolioMetrics(
            user_address=user_address,
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

    def _create_empty_performance_metrics(self) -> Dict[str, float]:
        """Create empty performance metrics."""
        return {
            "total_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "period_days": 0,
        }

    def _create_empty_risk_metrics(self) -> Dict[str, float]:
        """Create empty risk metrics."""
        return {
            "collateralization_ratio": 0.0,
            "utilization_rate": 0.0,
            "diversification_score": 0.0,
            "concentration_risk": 0.0,
            "aggregate_health_score": 0.0,
        }

    # ---------------------------------------------------------------------
    # Helper utilities
    # ---------------------------------------------------------------------

    @staticmethod
    def _to_dict(item):
        """Convert a Pydantic model or dataclass to a plain dict if needed."""
        if isinstance(item, dict):
            return item
        # Pydantic models have .model_dump in v2, .dict in v1 – try both
        if hasattr(item, "dict"):
            return item.dict()
        if hasattr(item, "model_dump"):
            return item.model_dump()
        # Fallback – try vars()
        return vars(item)
