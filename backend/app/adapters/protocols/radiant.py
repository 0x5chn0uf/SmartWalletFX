"""Radiant protocol adapter – interacts directly with on-chain contracts.

This class inherits :class:`ProtocolAdapter` so it can be injected into the
dynamic aggregator **and** still offers low-level helper methods used by the
`defi_radiant_usecase` module.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

import requests
from web3 import Web3

from app.abi.radiant_v2_abi import UI_POOL_DATA_PROVIDER_ABI
from app.core.config import settings
from app.schemas.defi import DeFiAccountSnapshot

from .base import ProtocolAdapter

__all__ = [
    "RadiantAdapterError",
    "RadiantContractAdapter",
]

# Default Radiant v2 contract addresses on Arbitrum – duplicated here to avoid
# reliance on the now-deprecated `app.constants.radiant` module.
DEFAULT_POOL_ADDRESS_PROVIDER: str = "0x454a8daf74b24037ee2fa073ce1be9277ed6160a"
DEFAULT_UI_POOL_DATA_PROVIDER: str = "0x56D4b07292343b149E0c60c7C41B7B1eEefdD733"

# ------------------------------------------------------------------
# Backwards-compatibility shim (tests still patch this symbol).  Remove once
# all tests have migrated to the class-based ABI injection approach.
# ------------------------------------------------------------------


class RadiantAdapterError(Exception):
    """Raised on RPC / data errors inside the Radiant adapter."""


class RadiantContractAdapter(ProtocolAdapter):
    """Adapter that talks to Radiant Capital contracts on Arbitrum."""

    name = "radiant"

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        *,
        pool_address_provider: Optional[str] = None,
        ui_pool_data_provider: Optional[str] = None,
        abi: Optional[list] = None,
    ) -> None:
        """Create a new :class:`RadiantContractAdapter`.

        Parameters
        ----------
        rpc_url
            Ethereum/Arbitrum JSON-RPC endpoint URL. Falls back to
            ``settings.ARBITRUM_RPC_URL`` when absent.
        pool_address_provider
            Address of the ``POOL_ADDRESS_PROVIDER`` contract.
        ui_pool_data_provider
            Address of the ``UI_POOL_DATA_PROVIDER`` contract.
        abi
            ABI list to use for the UI pool data provider. Defaults to the
            embedded ``UI_POOL_DATA_PROVIDER_ABI`` but can be overridden in
            tests to avoid large object patches.
        """

        self.rpc_url = rpc_url or settings.ARBITRUM_RPC_URL
        if not self.rpc_url:
            raise RadiantAdapterError("ARBITRUM_RPC_URL not set in config.")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        self.abi = abi or UI_POOL_DATA_PROVIDER_ABI

        # Allow callers/tests to override addresses easily
        ui_pool_data_provider = ui_pool_data_provider or DEFAULT_UI_POOL_DATA_PROVIDER
        pool_address_provider = pool_address_provider or DEFAULT_POOL_ADDRESS_PROVIDER

        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(ui_pool_data_provider),
            abi=self.abi,
        )

        self.provider = self.w3.to_checksum_address(pool_address_provider)

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

    def get_reserves_data(self) -> List[Dict[str, Any]]:
        """Get all reserves data from the contract."""
        try:
            result = self.contract.functions.getReservesData(self.provider).call()
            reserves: List[Dict[str, Any]] = []
            for r in result:
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
        except Exception as exc:
            raise RadiantAdapterError(f"get_reserves_data error: {exc}")

    def get_health_factor(self, user_address: str) -> float:
        """Get health factor for a specific user."""
        try:
            user_data = self.get_user_data(user_address)
            if user_data and "health_factor" in user_data:
                # Convert from wei (18 decimal places) to human-readable format
                health_factor_wei = user_data["health_factor"]
                return float(health_factor_wei) / (10**18)
            return 0.0
        except Exception as exc:
            raise RadiantAdapterError(f"get_health_factor error: {exc}")

    def get_user_summary(self, user_address: str) -> Dict[str, Any]:
        """Get a summary of user data including health factor."""
        try:
            user_data = self.get_user_data(user_address)
            if user_data:
                return {
                    "health_factor": user_data.get("health_factor", 0),
                    "reserves": user_data.get("reserves", []),
                }
            return {"health_factor": 0, "reserves": []}
        except Exception as exc:
            raise RadiantAdapterError(f"get_user_summary error: {exc}")

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
            and now - self._price_cache_time[token_address] < self._price_cache_ttl
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
