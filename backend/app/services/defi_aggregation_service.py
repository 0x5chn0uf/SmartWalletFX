"""
DeFi position aggregation service.

This service provides comprehensive DeFi position aggregation including:
- Multi-protocol position fetching
- Aggregate metrics calculation
- Caching and performance optimization
- Real-time DeFi data integration
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from app.adapters.defi_position import DeFiPositionAdapter
from app.models.aggregate_metrics import AggregateMetricsModel
from app.repositories.aggregate_metrics_repository import (
    AggregateMetricsRepository,
)

logger = logging.getLogger(__name__)


class DeFiAggregationService:
    """Service for aggregating DeFi positions across multiple protocols."""

    def __init__(self, db, redis_client=None):
        self.db = db
        self.redis = redis_client
        self.metrics_repo = AggregateMetricsRepository(db)
        self.position_adapter = DeFiPositionAdapter()

    async def aggregate_wallet_positions(
        self, wallet_address: str
    ) -> AggregateMetricsModel:
        """
        Aggregate all DeFi positions for a wallet address.

        Args:
            wallet_address: Ethereum wallet address to aggregate

        Returns:
            AggregateMetricsModel with calculated metrics
        """
        try:
            # Check cache first
            cached_metrics = await self._get_cached_metrics(wallet_address)
            if cached_metrics:
                logger.info(f"Cache hit for wallet {wallet_address}")
                return cached_metrics

            # Fetch positions from multiple protocols
            positions = await self.position_adapter.fetch_positions(wallet_address)

            # Create or get existing metrics
            metrics = await self._get_or_create_metrics(wallet_address)

            # Clear existing positions and recalculate
            metrics.positions = []
            metrics.tvl = 0.0
            metrics.total_borrowings = 0.0

            # Aggregate positions
            for position in positions:
                metrics.add_position(
                    protocol=position.get("protocol", "unknown"),
                    asset=position.get("asset", "unknown"),
                    amount=position.get("amount", 0.0),
                    usd_value=position.get("usd_value", 0.0),
                    apy=position.get("apy"),
                )

                # Track borrowings separately
                if position.get("type") == "borrowing":
                    metrics.total_borrowings += position.get("usd_value", 0.0)

            # Update aggregate APY
            metrics.update_aggregate_apy()

            # Save to database
            await self.metrics_repo.upsert(metrics)

            # Cache the result
            await self._cache_metrics(wallet_address, metrics)

            logger.info(
                f"Successfully aggregated {len(positions)} positions for "
                f"wallet {wallet_address}"
            )
            return metrics

        except Exception as e:
            logger.error(
                f"Error aggregating positions for wallet {wallet_address}: {str(e)}"
            )
            # Return empty metrics on error
            return await self._get_or_create_metrics(wallet_address)

    async def get_wallet_metrics(
        self, wallet_address: str
    ) -> Optional[AggregateMetricsModel]:
        """
        Get the latest aggregate metrics for a wallet.

        Args:
            wallet_address: Ethereum wallet address

        Returns:
            Latest AggregateMetricsModel or None if not found
        """
        return await self.metrics_repo.get_latest(wallet_address)

    async def get_wallet_history(
        self, wallet_address: str, limit: int = 100, offset: int = 0
    ) -> List[AggregateMetricsModel]:
        """
        Get historical aggregate metrics for a wallet.

        Args:
            wallet_address: Ethereum wallet address
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of historical AggregateMetricsModel instances
        """
        return await self.metrics_repo.get_history(wallet_address, limit, offset)

    async def refresh_wallet_metrics(
        self, wallet_address: str
    ) -> AggregateMetricsModel:
        """
        Force refresh of wallet metrics by clearing cache and recalculating.

        Args:
            wallet_address: Ethereum wallet address

        Returns:
            Freshly calculated AggregateMetricsModel
        """
        # Clear cache
        await self._clear_cache(wallet_address)

        # Recalculate
        return await self.aggregate_wallet_positions(wallet_address)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_or_create_metrics(
        self, wallet_address: str
    ) -> AggregateMetricsModel:
        """Get existing metrics or create new ones for a wallet."""
        existing = await self.metrics_repo.get_latest(wallet_address)
        if existing:
            return existing
        else:
            return AggregateMetricsModel.create_new(wallet_address)

    async def _get_cached_metrics(
        self, wallet_address: str
    ) -> Optional[AggregateMetricsModel]:
        """Get metrics from cache if available."""
        if not self.redis:
            return None

        try:
            cache_key = f"defi:aggregate:{wallet_address.lower()}"
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                metrics = AggregateMetricsModel.create_new(wallet_address)
                metrics.id = data.get("id")
                metrics.tvl = data.get("tvl", 0.0)
                metrics.total_borrowings = data.get("total_borrowings", 0.0)
                metrics.aggregate_apy = data.get("aggregate_apy")
                metrics.positions = data.get("positions", [])
                metrics.as_of = (
                    datetime.fromisoformat(data.get("as_of"))
                    if data.get("as_of")
                    else datetime.utcnow()
                )
                return metrics
        except Exception as e:
            logger.warning(f"Error reading from cache: {str(e)}")

        return None

    async def _cache_metrics(
        self, wallet_address: str, metrics: AggregateMetricsModel
    ) -> None:
        """Cache metrics for future requests."""
        if not self.redis:
            return

        try:
            cache_key = f"defi:aggregate:{wallet_address.lower()}"
            cache_data = metrics.to_dict()
            await self.redis.setex(
                cache_key, 300, json.dumps(cache_data)
            )  # 5 minutes TTL
        except Exception as e:
            logger.warning(f"Error caching metrics: {str(e)}")

    async def _clear_cache(self, wallet_address: str) -> None:
        """Clear cached metrics for a wallet."""
        if not self.redis:
            return

        try:
            cache_key = f"defi:aggregate:{wallet_address.lower()}"
            await self.redis.delete(cache_key)
        except Exception as e:
            logger.warning(f"Error clearing cache: {str(e)}")

    @staticmethod
    def validate_ethereum_address(address: str) -> bool:
        """
        Validate Ethereum address format.

        Args:
            address: Address to validate

        Returns:
            True if valid Ethereum address format
        """
        if not address:
            return False

        # Basic Ethereum address validation
        if not address.startswith("0x"):
            return False

        if len(address) != 42:  # 0x + 40 hex characters
            return False

        try:
            int(address[2:], 16)  # Check if rest is valid hex
            return True
        except ValueError:
            return False
