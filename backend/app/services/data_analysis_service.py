"""
Data analysis service for comprehensive portfolio and blockchain data analysis.

This service combines portfolio calculations and blockchain data to provide:
- Real-time portfolio analysis
- Historical performance tracking
- Risk assessment
- Market analysis
- Predictive analytics
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.services.blockchain_service import BlockchainService
from app.services.portfolio_service import PortfolioCalculationService

logger = logging.getLogger(__name__)


class DataAnalysisService:
    """Service for comprehensive data analysis combining portfolio
    and blockchain data."""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.portfolio_service = PortfolioCalculationService(db_session)
        self.blockchain_service = BlockchainService()

    async def analyze_portfolio_comprehensive(
        self,
        user_address: str,
        include_real_time: bool = True,
        include_historical: bool = True,
        include_predictions: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive portfolio analysis.

        Args:
            user_address: The user's wallet address
            include_real_time: Whether to include real-time blockchain data
            include_historical: Whether to include historical analysis
            include_predictions: Whether to include predictive analytics

        Returns:
            Comprehensive analysis results
        """
        try:
            analysis = {
                "user_address": user_address,
                "timestamp": datetime.utcnow(),
                "portfolio_metrics": None,
                "real_time_data": None,
                "historical_analysis": None,
                "risk_assessment": None,
                "performance_metrics": None,
                "predictions": None,
            }

            # Get portfolio metrics
            analysis[
                "portfolio_metrics"
            ] = await self.portfolio_service.calculate_portfolio_metrics(user_address)

            # Get real-time blockchain data
            if include_real_time:
                analysis["real_time_data"] = await self._get_real_time_data(
                    user_address
                )

            # Get historical analysis
            if include_historical:
                analysis["historical_analysis"] = await self._get_historical_analysis(
                    user_address
                )

            # Get risk assessment
            analysis[
                "risk_assessment"
            ] = await self.portfolio_service.calculate_risk_metrics(user_address)

            # Get performance metrics
            analysis[
                "performance_metrics"
            ] = self.portfolio_service.calculate_performance_metrics(user_address)

            # Get predictions (if enabled)
            if include_predictions:
                analysis["predictions"] = await self._generate_predictions(user_address)

            return analysis

        except Exception as e:
            logger.error(
                f"Error in comprehensive portfolio analysis for {user_address}: {e}"
            )
            return self._create_empty_analysis(user_address)

    async def analyze_market_trends(
        self, tokens: List[str], period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze market trends for specific tokens.

        Args:
            tokens: List of token addresses to analyze
            period_days: Number of days to analyze

        Returns:
            Market trend analysis
        """
        try:
            trends = {}

            for token_address in tokens:
                # Get historical price data
                historical_data = await self._get_token_historical_data(
                    token_address, period_days
                )

                if historical_data:
                    # Calculate trend metrics
                    trend_metrics = self._calculate_trend_metrics(historical_data)
                    trends[token_address] = trend_metrics

            return {
                "analysis_period": period_days,
                "tokens_analyzed": len(tokens),
                "trends": trends,
                "market_sentiment": self._calculate_market_sentiment(trends),
            }

        except Exception as e:
            logger.error(f"Error analyzing market trends: {e}")
            return {"trends": {}, "market_sentiment": "neutral"}

    async def generate_portfolio_insights(
        self, user_address: str
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable insights for a portfolio.

        Args:
            user_address: The user's wallet address

        Returns:
            List of insights with recommendations
        """
        try:
            insights = []

            # Get portfolio data
            portfolio_metrics = (
                await self.portfolio_service.calculate_portfolio_metrics(user_address)
            )
            risk_metrics = await self.portfolio_service.calculate_risk_metrics(
                user_address
            )
            performance_metrics = self.portfolio_service.calculate_performance_metrics(
                user_address
            )

            # Analyze health score
            if (
                portfolio_metrics.aggregate_health_score
                and portfolio_metrics.aggregate_health_score < 0.7
            ):
                insights.append(
                    {
                        "type": "health_score",
                        "severity": "high",
                        "title": "Low Health Score",
                        "description": (
                            "Your DeFi positions have a low health score,"
                            + "indicating potential liquidation risk."
                        ),
                        "recommendation": (
                            "Consider adding more collateral or reducing borrowings."
                        ),
                        "impact": "risk_management",
                    }
                )

            # Analyze performance
            if performance_metrics["total_return"] < 0:
                insights.append(
                    {
                        "type": "performance",
                        "severity": "medium",
                        "title": "Negative Performance",
                        "description": (
                            "Your portfolio has shown negative returns in the"
                            + "analyzed period."
                        ),
                        "recommendation": (
                            "Review your investment strategy and consider rebalancing."
                        ),
                        "impact": "performance_improvement",
                    }
                )

            # Analyze utilization rate
            if risk_metrics["utilization_rate"] > 0.8:
                insights.append(
                    {
                        "type": "utilization",
                        "severity": "high",
                        "title": "High Utilization Rate",
                        "description": (
                            "You're using a high percentage of your available"
                            + "borrowing capacity."
                        ),
                        "recommendation": (
                            "Consider reducing borrowings to maintain a safety margin."
                        ),
                        "impact": "risk_reduction",
                    }
                )

            # Analyze APY opportunities
            if (
                portfolio_metrics.aggregate_apy
                and portfolio_metrics.aggregate_apy < 0.05
            ):
                insights.append(
                    {
                        "type": "yield",
                        "severity": "low",
                        "title": "Low Yield Opportunities",
                        "description": "Your current yield is below market average.",
                        "recommendation": (
                            "Explore higher-yielding DeFi protocols or"
                            + "staking opportunities."
                        ),
                        "impact": "yield_optimization",
                    }
                )

            return insights

        except Exception as e:
            logger.error(f"Error generating portfolio insights for {user_address}: {e}")
            return []

    async def calculate_portfolio_efficiency(
        self, user_address: str
    ) -> Dict[str, float]:
        """
        Calculate portfolio efficiency metrics.

        Args:
            user_address: The user's wallet address

        Returns:
            Efficiency metrics
        """
        try:
            # Get portfolio data
            portfolio_metrics = (
                await self.portfolio_service.calculate_portfolio_metrics(user_address)
            )
            performance_metrics = self.portfolio_service.calculate_performance_metrics(
                user_address
            )

            # Calculate efficiency metrics
            sharpe_ratio = performance_metrics.get("sharpe_ratio", 0.0)
            health_score = portfolio_metrics.aggregate_health_score or 0.0

            # Calculate overall efficiency score (0-100)
            efficiency_score = (
                (sharpe_ratio * 0.6)  # 60% weight to risk-adjusted returns
                + (health_score * 0.4)  # 40% weight to health score
            ) * 100

            return {
                "efficiency_score": max(0, min(100, efficiency_score)),
                "sharpe_ratio": sharpe_ratio,
                "health_score": health_score,
                "risk_adjusted_return": sharpe_ratio,
                "portfolio_quality": health_score,
            }

        except Exception as e:
            logger.error(
                f"Error calculating portfolio efficiency for {user_address}: {e}"
            )
            return {
                "efficiency_score": 0.0,
                "sharpe_ratio": 0.0,
                "health_score": 0.0,
                "risk_adjusted_return": 0.0,
                "portfolio_quality": 0.0,
            }

    async def _get_real_time_data(self, user_address: str) -> Dict[str, Any]:
        """Get real-time blockchain data."""
        try:
            # Get current balances
            balances = await self.blockchain_service.get_wallet_balances(user_address)

            # Get DeFi positions
            defi_positions = await self.blockchain_service.get_defi_positions(
                user_address
            )

            # Calculate current portfolio value
            portfolio_value = await self.blockchain_service.calculate_portfolio_value(
                user_address
            )

            return {
                "balances": balances,
                "defi_positions": defi_positions,
                "portfolio_value": portfolio_value,
                "last_updated": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Error getting real-time data for {user_address}: {e}")
            return {}

    async def _get_historical_analysis(self, user_address: str) -> Dict[str, Any]:
        """Get historical analysis data."""
        try:
            # Get portfolio timeline
            timeline = await self.portfolio_service.calculate_portfolio_timeline(
                user_address, limit=90
            )

            # Get historical blockchain data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)
            historical_data = await self.blockchain_service.get_historical_data(
                user_address, start_date, end_date, "daily"
            )

            return {
                "timeline": timeline,
                "historical_data": historical_data,
                "analysis_period": "90_days",
                "data_points": len(historical_data),
            }

        except Exception as e:
            logger.error(f"Error getting historical analysis for {user_address}: {e}")
            return {}

    async def _generate_predictions(self, user_address: str) -> Dict[str, Any]:
        """Generate predictive analytics."""
        try:
            # This would typically use machine learning models
            # For now, return simple trend-based predictions

            # Get historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            historical_data = await self.blockchain_service.get_historical_data(
                user_address, start_date, end_date, "daily"
            )

            if not historical_data:
                return {"predictions": [], "confidence": 0.0}

            # Simple trend analysis
            values = [point["portfolio_value"] for point in historical_data]
            if len(values) >= 2:
                trend = (values[-1] - values[0]) / values[0]

                # Generate simple predictions
                current_value = values[-1]
                predictions = []

                for i in range(1, 8):  # 7-day prediction
                    predicted_value = current_value * (1 + trend * i / 30)
                    predictions.append(
                        {
                            "day": i,
                            "predicted_value": predicted_value,
                            "confidence": max(
                                0.1, 1.0 - (i * 0.1)
                            ),  # Decreasing confidence
                        }
                    )

                return {
                    "predictions": predictions,
                    "trend": trend,
                    "confidence": 0.7 if abs(trend) > 0.01 else 0.3,
                }

            return {"predictions": [], "confidence": 0.0}

        except Exception as e:
            logger.error(f"Error generating predictions for {user_address}: {e}")
            return {"predictions": [], "confidence": 0.0}

    async def _get_token_historical_data(
        self, token_address: str, period_days: int
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific token."""
        try:
            # This would integrate with price APIs
            # For now, return mock data
            data = []
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)

            current_date = start_date
            base_price = 100.0  # Mock base price

            while current_date <= end_date:
                # Generate mock price variation
                variation = (current_date.day % 30) / 30.0
                price = base_price * (1 + 0.2 * variation)

                data.append(
                    {
                        "timestamp": int(current_date.timestamp()),
                        "price": price,
                        "volume": 1000000 * (1 + 0.1 * variation),
                    }
                )

                current_date += timedelta(days=1)

            return data

        except Exception as e:
            logger.error(f"Error getting token historical data: {e}")
            return []

    def _calculate_trend_metrics(
        self, historical_data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate trend metrics from historical data."""
        try:
            if len(historical_data) < 2:
                return {}

            prices = [point["price"] for point in historical_data]

            # Calculate basic metrics
            start_price = prices[0]
            end_price = prices[-1]
            total_return = (end_price - start_price) / start_price

            # Calculate volatility
            returns = []
            for i in range(1, len(prices)):
                returns.append((prices[i] - prices[i - 1]) / prices[i - 1])

            if returns:
                volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5
            else:
                volatility = 0.0

            # Calculate trend strength
            trend_strength = abs(total_return) / volatility if volatility > 0 else 0.0

            return {
                "total_return": total_return,
                "volatility": volatility,
                "trend_strength": trend_strength,
                "start_price": start_price,
                "end_price": end_price,
                "price_change": end_price - start_price,
            }

        except Exception as e:
            logger.error(f"Error calculating trend metrics: {e}")
            return {}

    def _calculate_market_sentiment(self, trends: Dict[str, Dict[str, float]]) -> str:
        """Calculate overall market sentiment from trends."""
        try:
            if not trends:
                return "neutral"

            positive_trends = 0
            total_trends = len(trends)

            for trend_data in trends.values():
                if trend_data.get("total_return", 0) > 0:
                    positive_trends += 1

            positive_ratio = positive_trends / total_trends

            if positive_ratio > 0.7:
                return "bullish"
            elif positive_ratio < 0.3:
                return "bearish"
            else:
                return "neutral"

        except Exception as e:
            logger.error(f"Error calculating market sentiment: {e}")
            return "neutral"

    def _create_empty_analysis(self, user_address: str) -> Dict[str, Any]:
        """Create empty analysis result."""
        return {
            "user_address": user_address,
            "timestamp": datetime.utcnow(),
            "portfolio_metrics": None,
            "real_time_data": None,
            "historical_analysis": None,
            "risk_assessment": None,
            "performance_metrics": None,
            "predictions": None,
            "error": "Analysis failed",
        }
