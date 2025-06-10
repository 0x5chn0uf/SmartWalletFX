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


class RadiantAdapterError(Exception):
    pass


class RadiantContractAdapter:
    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or settings.ARBITRUM_RPC_URL
        if not self.rpc_url:
            raise RadiantAdapterError("ARBITRUM_RPC_URL not set in config.")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        try:
            with open(ABI_PATH) as f:
                self.abi = json.load(f)
        except Exception as e:
            raise RadiantAdapterError(f"Failed to load ABI: {e}")
        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(UI_POOL_DATA_PROVIDER),
            abi=self.abi,
        )
        self.provider = self.w3.to_checksum_address(POOL_ADDRESS_PROVIDER)
        self._price_cache = {}
        self._price_cache_time = {}
        self._price_cache_ttl = 60  # seconds
        # Token address to CoinGecko ID mapping (add more as needed)
        self._coingecko_map = {
            # USDC
            "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "usd-coin",
            # ETH (pseudo-address)
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE": "ethereum",
        }

    def get_user_data(self, user_address: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous contract call to fetch user reserves and health factor.
        """
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
                # (to be replaced with real price oracle)
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
        except Exception as e:
            raise RadiantAdapterError(f"RadiantContractAdapter error: {e}")

    async def async_get_user_data(
        self, user_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        Async wrapper for get_user_data using asyncio.to_thread.
        """
        return await asyncio.to_thread(self.get_user_data, user_address)

    def get_token_metadata(self, token_address: str) -> (str, int):
        """
        Fetch ERC20 symbol and decimals for a token address.
        """
        try:
            token = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token_address),
                abi=ERC20_ABI,
            )
            symbol = token.functions.symbol().call()
            decimals = token.functions.decimals().call()
            return symbol, decimals
        except Exception:
            return "UNKNOWN", 18

    def get_token_price(self, token_address: str) -> float:
        """
        Fetch token price in USD using CoinGecko. Caches for 60s.
        Returns 1.0 if unknown.
        """
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
                f"https://api.coingecko.com/api/v3/simple/price?ids="
                f"{coingecko_id}&vs_currencies=usd"
            )
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            price = resp.json()[coingecko_id]["usd"]
            self._price_cache[token_address] = price
            self._price_cache_time[token_address] = now
            return price
        except Exception:
            return 1.0

    def to_usd(
        self, amount: int, symbol: str, token_address: Optional[str] = None
    ) -> float:
        """
        Convert token amount to USD using price oracle.
        If token_address is provided, use real price.
        """
        if token_address:
            price = self.get_token_price(token_address)
            return float(amount) * price
        return float(amount)

    def get_reserves_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch protocol-wide reserves data (rates, liquidity, etc.)
        """
        try:
            reserves_data = self.contract.functions.getReservesData(
                self.provider
            ).call()
            # reserves_data is a tuple: (reserves_list, ...)
            reserves_list = (
                reserves_data[0]
                if isinstance(reserves_data, (list, tuple))
                else reserves_data
            )
            reserves = []
            for r in reserves_list:
                token_address = r[0]
                symbol, decimals = self.get_token_metadata(token_address)
                reserves.append(
                    {
                        "token_address": token_address,
                        "symbol": symbol,
                        "decimals": decimals,
                        # Add more fields as needed from ABI
                    }
                )
            return reserves
        except Exception as e:
            raise RadiantAdapterError(f"get_reserves_data error: {e}")

    def get_health_factor(self, user_address: str) -> Optional[float]:
        """
        Fetch only the health factor for a user.
        """
        try:
            user = self.w3.to_checksum_address(user_address)
            result = self.contract.functions.getUserReservesData(
                self.provider, user
            ).call()
            _, health_factor = result
            return float(health_factor)
        except Exception as e:
            raise RadiantAdapterError(f"get_health_factor error: {e}")

    def get_user_summary(self, user_address: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user reserves and health factor in a single call (summary).
        """
        try:
            user = self.w3.to_checksum_address(user_address)
            result = self.contract.functions.getUserReservesData(
                self.provider, user
            ).call()
            reserves_raw, health_factor = result
            return {
                "reserves": reserves_raw,
                "health_factor": health_factor,
            }
        except Exception as e:
            raise RadiantAdapterError(f"get_user_summary error: {e}")
