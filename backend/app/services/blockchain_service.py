"""
Blockchain data retrieval and calculation service.

This service handles:
- Blockchain data fetching
- Smart contract interactions
- Token price calculations
- Historical data retrieval
- Real-time balance calculations
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from web3 import Web3

from app.core.config import settings
from app.schemas.defi import ProtocolName

logger = logging.getLogger(__name__)


class BlockchainService:
    """Service for blockchain data retrieval and calculations."""

    def __init__(self):
        self.w3 = None
        self._setup_web3()

    def _setup_web3(self):
        """Setup Web3 connection."""
        try:
            if settings.WEB3_PROVIDER_URI:
                self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
                if not self.w3.is_connected():
                    logger.warning("Failed to connect to Ethereum RPC")
                    self.w3 = None
            else:
                self.w3 = None
        except Exception as e:
            logger.error(f"Error setting up Web3: {e}")
            self.w3 = None

    async def get_wallet_balances(
        self, wallet_address: str, tokens: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get current balances for a wallet.

        Args:
            wallet_address: The wallet address to query
            tokens: Optional list of token addresses to query

        Returns:
            Dictionary with token balances
        """
        try:
            if not self.w3:
                return {}

            balances = {}

            # If no specific tokens provided, get balances for common tokens
            if not tokens:
                tokens = self._get_common_tokens()

            for token_address in tokens:
                try:
                    # Create contract instance
                    contract = self.w3.eth.contract(
                        address=Web3.to_checksum_address(token_address),
                        abi=self._get_erc20_abi(),
                    )

                    # Get balance
                    balance = await self._get_token_balance_async(
                        contract, wallet_address
                    )

                    if balance > 0:
                        balances[token_address] = {
                            "balance": str(balance),
                            "balance_wei": balance,
                            "decimals": await self._get_token_decimals_async(contract),
                        }

                except Exception as e:
                    logger.warning(
                        f"Error getting balance for token {token_address}: {e}"
                    )
                    continue

            return balances

        except Exception as e:
            logger.error(f"Error getting wallet balances for {wallet_address}: {e}")
            return {}

    async def get_token_price(
        self, token_address: str, currency: str = "USD"
    ) -> Optional[float]:
        """
        Get token price from price oracle.

        Args:
            token_address: The token address
            currency: The currency to get price in

        Returns:
            Token price or None if not available
        """
        try:
            # Try multiple price sources
            price = await self._get_price_from_coingecko(token_address, currency)
            if price:
                return price

            price = await self._get_price_from_chainlink(token_address, currency)
            if price:
                return price

            # Fallback to hardcoded prices for common tokens
            return self._get_hardcoded_price(token_address, currency)

        except Exception as e:
            logger.error(f"Error getting price for token {token_address}: {e}")
            return None

    async def get_defi_positions(self, wallet_address: str) -> Dict[str, Any]:
        """
        Get DeFi positions for a wallet across multiple protocols.

        Args:
            wallet_address: The wallet address

        Returns:
            Dictionary with DeFi positions
        """
        try:
            positions = {
                "collaterals": [],
                "borrowings": [],
                "staked_positions": [],
                "health_scores": [],
            }

            # Get Aave positions
            aave_positions = await self._get_aave_positions(wallet_address)
            positions["collaterals"].extend(aave_positions.get("collaterals", []))
            positions["borrowings"].extend(aave_positions.get("borrowings", []))
            positions["health_scores"].extend(aave_positions.get("health_scores", []))

            # Get Compound positions
            compound_positions = await self._get_compound_positions(wallet_address)
            positions["collaterals"].extend(compound_positions.get("collaterals", []))
            positions["borrowings"].extend(compound_positions.get("borrowings", []))
            positions["health_scores"].extend(
                compound_positions.get("health_scores", [])
            )

            # Get staking positions
            staking_positions = await self._get_staking_positions(wallet_address)
            positions["staked_positions"].extend(staking_positions)

            return positions

        except Exception as e:
            logger.error(f"Error getting DeFi positions for {wallet_address}: {e}")
            return {
                "collaterals": [],
                "borrowings": [],
                "staked_positions": [],
                "health_scores": [],
            }

    async def calculate_portfolio_value(self, wallet_address: str) -> Dict[str, float]:
        """
        Calculate total portfolio value in USD.

        Args:
            wallet_address: The wallet address

        Returns:
            Dictionary with portfolio values
        """
        try:
            # Get token balances
            balances = await self.get_wallet_balances(wallet_address)

            total_value = 0.0
            token_values = {}

            for token_address, balance_data in balances.items():
                # Get token price
                price = await self.get_token_price(token_address)

                # Calculate value
                balance_wei = balance_data["balance_wei"]
                decimals = balance_data["decimals"]
                balance = balance_wei / (10**decimals)

                if price:
                    value = balance * price
                    total_value += value
                else:
                    value = 0.0

                # Always add token to token_values
                token_values[token_address] = {
                    "balance": balance,
                    "price": price,
                    "value": value,
                }

            return {"total_value": total_value, "token_values": token_values}

        except Exception as e:
            logger.error(f"Error calculating portfolio value for {wallet_address}: {e}")
            return {"total_value": 0.0, "token_values": {}}

    async def get_historical_data(
        self,
        wallet_address: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "daily",
    ) -> List[Dict[str, Any]]:
        """
        Get historical portfolio data.

        Args:
            wallet_address: The wallet address
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval (daily, weekly, monthly)

        Returns:
            List of historical data points
        """
        try:
            # This would typically integrate with external APIs like:
            # - Etherscan API for transaction history
            # - DeFi protocol APIs for historical positions
            # - Price APIs for historical prices

            # For now, return mock data
            return self._generate_mock_historical_data(
                wallet_address, start_date, end_date, interval
            )

        except Exception as e:
            logger.error(f"Error getting historical data for {wallet_address}: {e}")
            return []

    def _get_common_tokens(self) -> List[str]:
        """Get list of common token addresses."""
        return [
            "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C80",  # USDC (fixed to 42 chars)
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
        ]

    def _get_erc20_abi(self) -> List[Dict]:
        """Get minimal ERC20 ABI for balance and decimals calls."""
        return [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
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

    async def _get_token_balance_async(self, contract, wallet_address: str) -> int:
        """Get token balance asynchronously."""
        try:
            balance = contract.functions.balanceOf(
                Web3.to_checksum_address(wallet_address)
            ).call()
            return balance
        except Exception as e:
            logger.warning(f"Error getting token balance: {e}")
            return 0

    async def _get_token_decimals_async(self, contract) -> int:
        """Get token decimals asynchronously."""
        try:
            decimals = contract.functions.decimals().call()
            return decimals
        except Exception as e:
            logger.warning(f"Error getting token decimals: {e}")
            return 18

    async def _get_price_from_coingecko(
        self, token_address: str, currency: str
    ) -> Optional[float]:
        """Get token price from CoinGecko API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
                params = {
                    "contract_addresses": token_address,
                    "vs_currencies": currency.lower(),
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if token_address.lower() in data:
                            return data[token_address.lower()][currency.lower()]

            return None

        except Exception as e:
            logger.warning(f"Error getting price from CoinGecko: {e}")
            return None

    async def _get_price_from_chainlink(
        self, token_address: str, currency: str
    ) -> Optional[float]:
        """Get token price from Chainlink price feeds."""
        try:
            if not self.w3:
                return None

            # Chainlink price feed addresses (simplified)
            price_feeds = {
                "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C80": (
                    "0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6"  # USDC/USD
                ),
                "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": (
                    "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c"  # BTC/USD
                ),
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": (
                    "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"  # ETH/USD
                ),
            }

            if token_address not in price_feeds:
                return None

            feed_address = price_feeds[token_address]
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(feed_address),
                abi=self._get_chainlink_abi(),
            )

            # Get latest price
            price_data = contract.functions.latestRoundData().call()
            price = price_data[1] / 10**8  # Chainlink prices have 8 decimals

            return price

        except Exception as e:
            logger.warning(f"Error getting price from Chainlink: {e}")
            return None

    def _get_hardcoded_price(
        self, token_address: str, currency: str
    ) -> Optional[float]:
        """Get hardcoded prices for common tokens."""
        prices = {
            "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C80": 1.0,  # USDC
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": 45000.0,  # WBTC
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": 3000.0,  # WETH
            "0xdAC17F958D2ee523a2206206994597C13D831ec7": 1.0,  # USDT
            "0x6B175474E89094C44Da98b954EedeAC495271d0F": 1.0,  # DAI
        }

        return prices.get(token_address)

    def _get_chainlink_abi(self) -> List[Dict]:
        """Get Chainlink price feed ABI."""
        return [
            {
                "inputs": [],
                "name": "latestRoundData",
                "outputs": [
                    {"name": "roundId", "type": "uint80"},
                    {"name": "answer", "type": "int256"},
                    {"name": "startedAt", "type": "uint256"},
                    {"name": "updatedAt", "type": "uint256"},
                    {"name": "answeredInRound", "type": "uint80"},
                ],
                "stateMutability": "view",
                "type": "function",
            }
        ]

    async def _get_aave_positions(self, wallet_address: str) -> Dict[str, List]:
        """Get Aave protocol positions."""
        try:
            # This would integrate with Aave protocol contracts
            # For now, return mock data
            return {
                "collaterals": [
                    {
                        "protocol": ProtocolName.aave,
                        "asset": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                        "amount": 1.5,
                        "usd_value": 4500.0,
                    }
                ],
                "borrowings": [
                    {
                        "protocol": ProtocolName.aave,
                        "asset": "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8",
                        "amount": 1000.0,
                        "usd_value": 1000.0,
                        "interest_rate": 0.05,
                    }
                ],
                "health_scores": [{"protocol": ProtocolName.aave, "score": 0.85}],
            }
        except Exception as e:
            logger.error(f"Error getting Aave positions: {e}")
            return {"collaterals": [], "borrowings": [], "health_scores": []}

    async def _get_compound_positions(self, wallet_address: str) -> Dict[str, List]:
        """Get Compound protocol positions."""
        try:
            # This would integrate with Compound protocol contracts
            # For now, return mock data
            return {
                "collaterals": [
                    {
                        "protocol": ProtocolName.compound,
                        "asset": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                        "amount": 0.1,
                        "usd_value": 4500.0,
                    }
                ],
                "borrowings": [
                    {
                        "protocol": ProtocolName.compound,
                        "asset": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                        "amount": 500.0,
                        "usd_value": 500.0,
                        "interest_rate": 0.03,
                    }
                ],
                "health_scores": [{"protocol": ProtocolName.compound, "score": 0.92}],
            }
        except Exception as e:
            logger.error(f"Error getting Compound positions: {e}")
            return {"collaterals": [], "borrowings": [], "health_scores": []}

    async def _get_staking_positions(self, wallet_address: str) -> List[Dict]:
        """Get staking positions."""
        try:
            # This would integrate with various staking protocols
            # For now, return mock data
            return [
                {
                    "protocol": ProtocolName.aave,
                    "asset": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                    "amount": 10.0,
                    "usd_value": 1000.0,
                    "apy": 0.08,
                }
            ]
        except Exception as e:
            logger.error(f"Error getting staking positions: {e}")
            return []

    def _generate_mock_historical_data(
        self,
        wallet_address: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> List[Dict[str, Any]]:
        """Generate mock historical data for testing."""
        data = []
        current_date = start_date

        while current_date <= end_date:
            # Generate mock portfolio value
            base_value = 10000.0
            variation = (current_date.day % 30) / 30.0  # Simple variation based on day
            portfolio_value = base_value * (1 + 0.1 * variation)

            data.append(
                {
                    "timestamp": int(current_date.timestamp()),
                    "date": current_date.isoformat(),
                    "portfolio_value": portfolio_value,
                    "value": portfolio_value,
                    "collateral_value": portfolio_value * 0.8,
                    "borrowing_value": portfolio_value * 0.2,
                    "health_score": 0.85 + (0.1 * variation),
                }
            )

            # Move to next interval
            if interval == "daily":
                current_date += timedelta(days=1)
            elif interval == "weekly":
                current_date += timedelta(weeks=1)
            elif interval == "monthly":
                current_date += timedelta(days=30)
            else:
                # Default to daily for invalid intervals
                current_date += timedelta(days=1)

        return data
