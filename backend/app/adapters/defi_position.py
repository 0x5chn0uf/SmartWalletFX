"""
DeFi position adapter for fetching positions from multiple protocols.

This adapter provides a unified interface for fetching DeFi positions
from various protocols like Aave, Compound, Uniswap, etc.
"""

import asyncio
import logging
from typing import Any, Dict, List

from app.adapters.protocols.aave import AaveContractAdapter
from app.adapters.protocols.compound import CompoundContractAdapter
from app.adapters.protocols.radiant import RadiantContractAdapter

logger = logging.getLogger(__name__)


class DeFiPositionAdapter:
    """Adapter for fetching DeFi positions from external APIs and protocols."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def fetch_positions(self, wallet_address: str) -> List[Dict[str, Any]]:
        """
        Fetch all DeFi positions for a wallet address from multiple protocols.

        Args:
            wallet_address: The wallet address to fetch positions for

        Returns:
            List of position dictionaries with protocol, asset, amount, and value info
        """
        try:
            # Fetch positions from multiple protocols concurrently
            tasks = [
                self._fetch_aave_positions(wallet_address),
                self._fetch_compound_positions(wallet_address),
                self._fetch_radiant_positions(wallet_address),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Combine all positions
            all_positions = []
            for result in results:
                if isinstance(result, list):
                    all_positions.extend(result)
                elif isinstance(result, Exception):
                    self.logger.warning(f"Error fetching positions: {result}")

            return all_positions

        except Exception as e:
            self.logger.error(f"Error fetching DeFi positions: {e}")
            return []

    async def _fetch_aave_positions(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Fetch positions from Aave protocol."""
        try:
            adapter = AaveContractAdapter()
            snapshot = await adapter.get_user_snapshot(wallet_address)

            if not snapshot:
                return []

            positions = []

            # Add supply positions
            for supply in snapshot.supplies or []:
                positions.append(
                    {
                        "protocol": "aave",
                        "asset": supply.asset,
                        "amount": supply.amount,
                        "usd_value": supply.usd_value,
                        "apy": supply.apy,
                        "type": "supply",
                    }
                )

            # Add borrow positions
            for borrow in snapshot.borrows or []:
                positions.append(
                    {
                        "protocol": "aave",
                        "asset": borrow.asset,
                        "amount": borrow.amount,
                        "usd_value": borrow.usd_value,
                        "apy": borrow.apy,
                        "type": "borrow",
                    }
                )

            return positions

        except Exception as e:
            self.logger.error(f"Error fetching Aave positions: {e}")
            return []

    async def _fetch_compound_positions(
        self, wallet_address: str
    ) -> List[Dict[str, Any]]:
        """Fetch positions from Compound protocol."""
        try:
            adapter = CompoundContractAdapter()
            snapshot = await adapter.get_user_snapshot(wallet_address)

            if not snapshot:
                return []

            positions = []

            # Add supply positions
            for supply in snapshot.supplies or []:
                positions.append(
                    {
                        "protocol": "compound",
                        "asset": supply.asset,
                        "amount": supply.amount,
                        "usd_value": supply.usd_value,
                        "apy": supply.apy,
                        "type": "supply",
                    }
                )

            # Add borrow positions
            for borrow in snapshot.borrows or []:
                positions.append(
                    {
                        "protocol": "compound",
                        "asset": borrow.asset,
                        "amount": borrow.amount,
                        "usd_value": borrow.usd_value,
                        "apy": borrow.apy,
                        "type": "borrow",
                    }
                )

            return positions

        except Exception as e:
            self.logger.error(f"Error fetching Compound positions: {e}")
            return []

    async def _fetch_radiant_positions(
        self, wallet_address: str
    ) -> List[Dict[str, Any]]:
        """Fetch positions from Radiant protocol."""
        try:
            adapter = RadiantContractAdapter()
            snapshot = await adapter.get_user_snapshot(wallet_address)

            if not snapshot:
                return []

            positions = []

            # Add supply positions
            for supply in snapshot.supplies or []:
                positions.append(
                    {
                        "protocol": "radiant",
                        "asset": supply.asset,
                        "amount": supply.amount,
                        "usd_value": supply.usd_value,
                        "apy": supply.apy,
                        "type": "supply",
                    }
                )

            # Add borrow positions
            for borrow in snapshot.borrows or []:
                positions.append(
                    {
                        "protocol": "radiant",
                        "asset": borrow.asset,
                        "amount": borrow.amount,
                        "usd_value": borrow.usd_value,
                        "apy": borrow.apy,
                        "type": "borrow",
                    }
                )

            return positions

        except Exception as e:
            self.logger.error(f"Error fetching Radiant positions: {e}")
            return []

    def calculate_aggregate_metrics(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate aggregate metrics from a list of positions.

        Args:
            positions: List of position dictionaries

        Returns:
            Dictionary containing aggregate metrics
        """
        if not positions:
            return {
                "tvl": 0.0,
                "total_borrowings": 0.0,
                "aggregate_apy": None,
                "positions": [],
            }

        tvl = 0.0
        total_borrowings = 0.0
        total_supply_value = 0.0
        total_supply_apy = 0.0
        supply_count = 0

        for position in positions:
            usd_value = position.get("usd_value", 0) or 0
            apy = position.get("apy")

            if position.get("type") == "supply":
                tvl += usd_value
                total_supply_value += usd_value
                if apy is not None:
                    total_supply_apy += usd_value * apy
                    supply_count += 1
            elif position.get("type") == "borrow":
                total_borrowings += usd_value

        # Calculate weighted average APY
        aggregate_apy = None
        if total_supply_value > 0 and supply_count > 0:
            aggregate_apy = total_supply_apy / total_supply_value

        return {
            "tvl": tvl,
            "total_borrowings": total_borrowings,
            "aggregate_apy": aggregate_apy,
            "positions": positions,
        }
