"""Radiant protocol adapter – interacts directly with on-chain contracts.

This class inherits :class:`ProtocolAdapter` so it can be injected into the
dynamic aggregator **and** still offers low-level helper methods used by the
`defi_radiant_usecase` module.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import requests
from web3 import Web3

from app.constants.radiant import (
    ABI_PATH,
    POOL_ADDRESS_PROVIDER,
    UI_POOL_DATA_PROVIDER,
)
from app.core.config import settings
from app.schemas.defi import DeFiAccountSnapshot

from .base import ProtocolAdapter

__all__ = [
    "RadiantAdapterError",
    "RadiantContractAdapter",
]


class RadiantAdapterError(Exception):
    """Raised on RPC / data errors inside the Radiant adapter."""


class RadiantContractAdapter(ProtocolAdapter):
    """Adapter that talks to Radiant Capital contracts on Arbitrum."""

    name = "radiant"
    display_name = "Radiant"

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or settings.ARBITRUM_RPC_URL
        if not self.rpc_url:
            raise RadiantAdapterError("ARBITRUM_RPC_URL not set in config.")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        try:
            with open(ABI_PATH) as f:
                self.abi = json.load(f)
        except Exception as exc:  # pragma: no cover – config issue
            raise RadiantAdapterError(f"Failed to load ABI: {exc}")

        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(UI_POOL_DATA_PROVIDER),
            abi=self.abi,
        )
        self.provider = self.w3.to_checksum_address(POOL_ADDRESS_PROVIDER)

        self._price_cache: dict[str, float] = {}
        self._price_cache_time: dict[str, float] = {}
        self._price_cache_ttl = 60  # seconds

        # Token address to CoinGecko ID mapping (add more as needed)
        self._coingecko_map: dict[str, str] = {
            # USDC
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "usd-coin",
            # ETH (pseudo-address)
            "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee": "ethereum",
        }

    # ------------------------------------------------------------------
    # ProtocolAdapter public API
    # ------------------------------------------------------------------

    async def fetch_snapshot(
        self, address: str
    ) -> Optional[DeFiAccountSnapshot]:  # noqa: D401
        """Delegate to high-level use-case to convert raw data → snapshot."""

        from app.usecase.defi_radiant_usecase import RadiantUsecase

        usecase = RadiantUsecase()
        return await usecase.get_user_snapshot(address)

    # ------------------------------------------------------------------
    # Low-level contract helpers (existing functionality)
    # ------------------------------------------------------------------

    def get_user_data(self, user_address: str) -> Optional[Dict[str, Any]]:
        """Sync contract call for user reserves and health factor."""

        try:
            user = self.w3.to_checksum_address(user_address)
            result = self.contract.functions.getUserReservesData(
                self.provider, user
            ).call()
            reserves_raw, health_factor = result
            reserves: List[Dict[str, Any]] = []
            for r in reserves_raw:
                token_address = r[0]
                supplied = r[1]
                used_as_collateral = r[2]
                variable_borrowed = r[4] if len(r) > 4 else r[3]
                stable_borrowed = r[5] if len(r) > 5 else 0
                # Fetch token metadata
                symbol, decimals = self.get_token_metadata(token_address)
                # Placeholder for USD value
                usd_value = self.to_usd(supplied, symbol, token_address)
                reserves.append(
                    {
                        "token_address": token_address,
                        "symbol": symbol,
                        "decimals": decimals,
                        "supplied": supplied,
                        "supplied_usd": usd_value,
                        "used_as_collateral": used_as_collateral,
                        "variable_borrowed": variable_borrowed,
                        "stable_borrowed": stable_borrowed,
                    }
                )
            return {
                "reserves": reserves,
                "health_factor": health_factor,
            }
        except Exception as exc:  # pragma: no cover – runtime error
            raise RadiantAdapterError(f"RadiantContractAdapter error: {exc}")

    async def async_get_user_data(
        self, user_address: str
    ) -> Optional[Dict[str, Any]]:  # noqa: D401
        """Async wrapper for ``get_user_data`` using a thread-offload."""

        return await asyncio.to_thread(self.get_user_data, user_address)

    # ----------------------------- helpers -----------------------------

    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function",
        },
    ]

    def get_token_metadata(self, token_address: str) -> tuple[str, int]:
        """Return ERC-20 symbol & decimals (falls back to UNKNOWN/18)."""

        try:
            token = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token_address),
                abi=self.ERC20_ABI,
            )
            symbol = token.functions.symbol().call()
            decimals = token.functions.decimals().call()
            return symbol, decimals
        except Exception:  # pragma: no cover – token metadata failure
            return "UNKNOWN", 18

    # -------------------- CoinGecko / price helpers -------------------

    def get_token_price(self, token_address: str) -> float:  # noqa: D401
        """Return USD price (placeholder fallback=1.0)."""

        now = time.time()
        token_address = token_address.lower()
        if (
            token_address in self._price_cache
            and now - self._price_cache_time[token_address]
            < self._price_cache_ttl
        ):
            return self._price_cache[token_address]

        coingecko_id = self._coingecko_map.get(token_address)
        if not coingecko_id:
            return 1.0

        try:
            url = (
                "https://api.coingecko.com/api/v3/simple/price?ids="
                f"{coingecko_id}&vs_currencies=usd"
            )
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            price = resp.json()[coingecko_id]["usd"]
            self._price_cache[token_address] = price
            self._price_cache_time[token_address] = now
            return price
        except Exception:  # pragma: no cover – network error
            return 1.0

    def to_usd(
        self, amount: int, symbol: str, token_address: Optional[str] = None
    ) -> float:  # noqa: D401
        """Convert *amount* to USD using cached price oracle."""

        if token_address:
            price = self.get_token_price(token_address)
            return float(amount) * price
        return float(amount)

    # ---------------- protocol-wide helper calls ----------------------

    def get_reserves_data(self) -> Optional[List[Dict[str, Any]]]:
        try:
            reserves_data = self.contract.functions.getReservesData(
                self.provider
            ).call()
            reserves_list = (
                reserves_data[0]
                if isinstance(reserves_data, (list, tuple))
                else reserves_data
            )
            reserves: list[dict[str, Any]] = []
            for r in reserves_list:
                token_address = r[0]
                symbol, decimals = self.get_token_metadata(token_address)
                reserves.append(
                    {
                        "token_address": token_address,
                        "symbol": symbol,
                        "decimals": decimals,
                    }
                )
            return reserves
        except Exception as exc:  # pragma: no cover
            raise RadiantAdapterError(f"get_reserves_data error: {exc}")

    def get_health_factor(self, user_address: str) -> Optional[float]:
        try:
            user = self.w3.to_checksum_address(user_address)
            result = self.contract.functions.getUserReservesData(
                self.provider, user
            ).call()
            return float(result[1]) / 1e18 if result else None
        except Exception as exc:  # pragma: no cover
            raise RadiantAdapterError(f"get_health_factor error: {exc}")

    def get_user_summary(self, user_address: str) -> Optional[Dict[str, Any]]:
        try:
            user = self.w3.to_checksum_address(user_address)
            user_data = self.get_user_data(user)
            if not user_data:
                return None
            return {
                "health_factor": user_data["health_factor"],
                "reserves": user_data["reserves"],
            }
        except Exception as exc:  # pragma: no cover
            raise RadiantAdapterError(f"get_user_summary error: {exc}")