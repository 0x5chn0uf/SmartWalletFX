"""
Compound DeFi Use Case Logic

This module provides the use case for fetching and mapping Compound
user data (Ethereum mainnet). It exposes a function
to retrieve a DeFiAccountSnapshot for a given address, using the agnostic
backend models.
"""
import logging
from datetime import datetime
from typing import Optional

from web3 import Web3

from app.abi.compound_v2_abi import (
    COMPOUND_COMPTROLLER_ABI,
    COMPOUND_CTOKEN_ABI,
)
from app.schemas.defi import (
    Borrowing,
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
)

COMPOUND_COMPTROLLER_ADDRESS = "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"
COMPOUND_DECIMALS = 10**18


class CompoundUsecase:
    def __init__(self, w3: Optional[Web3] = None):
        """Create the use-case.

        If *w3* is *None*, a new :class:`web3.Web3` instance is created from
        configuration values.  Keeping the parameter optional aligns with the
        unit-tests that instantiate the class directly without passing a
        provider.
        """

        if w3 is None:
            from app.core.config import settings

            provider_uri = (
                settings.WEB3_PROVIDER_URI
                or settings.ARBITRUM_RPC_URL
                or "https://ethereum-rpc.publicnode.com"
            )
            w3 = Web3(Web3.HTTPProvider(provider_uri))

        self.w3 = w3

    async def get_user_snapshot(self, user_address: str) -> DeFiAccountSnapshot | None:
        try:
            checksum_address = self.w3.to_checksum_address(user_address)
            comptroller = self.w3.eth.contract(
                address=self.w3.to_checksum_address(COMPOUND_COMPTROLLER_ADDRESS),
                abi=COMPOUND_COMPTROLLER_ABI,
            )

            assets = comptroller.functions.getAssetsIn(checksum_address).call()
            total_collateral_usd = 0
            total_borrowings_usd = 0

            for asset_address in assets:
                c_token = self.w3.eth.contract(
                    address=asset_address, abi=COMPOUND_CTOKEN_ABI
                )
                balance = c_token.functions.balanceOf(checksum_address).call()
                borrow_balance = c_token.functions.borrowBalanceCurrent(
                    checksum_address
                ).call()
                exchange_rate = c_token.functions.exchangeRateCurrent().call()

                collateral_factor = comptroller.functions.markets(asset_address).call()[
                    1
                ]

                underlying_price = 1  # Simplified: assume 1 USD for simplicity
                token_balance = (
                    balance * exchange_rate / COMPOUND_DECIMALS
                ) * underlying_price
                total_collateral_usd += (
                    token_balance * collateral_factor / COMPOUND_DECIMALS
                )
                total_borrowings_usd += borrow_balance / COMPOUND_DECIMALS

            _, liquidity, shortfall = comptroller.functions.getAccountLiquidity(
                checksum_address
            ).call()
            health_factor = (
                (liquidity / total_borrowings_usd) if total_borrowings_usd > 0 else 0
            )

            return DeFiAccountSnapshot(
                user_address=user_address,
                timestamp=int(datetime.utcnow().timestamp()),
                collaterals=[
                    Collateral(
                        protocol=ProtocolName.compound,
                        asset="various",
                        amount=total_collateral_usd,
                        usd_value=total_collateral_usd,
                    )
                ],
                borrowings=[
                    Borrowing(
                        protocol=ProtocolName.compound,
                        asset="various",
                        amount=total_borrowings_usd,
                        usd_value=total_borrowings_usd,
                        interest_rate=None,
                    )
                ],
                staked_positions=[],
                health_scores=[
                    HealthScore(protocol=ProtocolName.compound, score=health_factor)
                ],
            )
        except Exception:
            logging.warning(
                "Could not fetch Compound snapshot for %s",
                user_address,
                exc_info=True,
            )

            return None
