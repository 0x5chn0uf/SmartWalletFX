"""
Aave DeFi Use Case Logic

This module provides the use case for fetching and mapping Aave user data
from the subgraph (Ethereum mainnet). It exposes a function to retrieve
a DeFiAccountSnapshot for a given address, using the agnostic backend models.
"""
import logging
from datetime import datetime
from typing import Optional
from web3 import Web3
from app.abi.aave_v2_abi import (
    AAVE_LENDING_POOL_V2_ABI,
    AAVE_POOL_ADDRESS_PROVIDER_ABI,
)
from app.schemas.defi import (
    Borrowing,
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
    StakedPosition,
)

AAVE_POOL_ADDRESS_PROVIDER_ADDRESS = "0xB53C1a33016B2DC2fF3653530bfF1848a515c8c5"
AAVE_DECIMALS = 10**18


class AaveUsecase:
    def __init__(self, w3: Web3):
        self.w3 = w3

    async def get_user_snapshot(
        self, user_address: str
    ) -> DeFiAccountSnapshot | None:
        try:
            checksum_address = self.w3.to_checksum_address(user_address)
            pool_addresses_provider = self.w3.eth.contract(
                address=self.w3.to_checksum_address(
                    AAVE_POOL_ADDRESS_PROVIDER_ADDRESS
                ),
                abi=AAVE_POOL_ADDRESS_PROVIDER_ABI,
            )
            lending_pool_address = pool_addresses_provider.functions.getPool().call()
            lending_pool = self.w3.eth.contract(
                address=lending_pool_address, abi=AAVE_LENDING_POOL_V2_ABI
            )
            (
                total_collateral,
                total_debt,
                _,
                _,
                _,
                health_factor,
            ) = lending_pool.functions.getUserAccountData(
                checksum_address
            ).call()

            total_collateral_usd = total_collateral / AAVE_DECIMALS
            total_debt_usd = total_debt / AAVE_DECIMALS

            return DeFiAccountSnapshot(
                user_address=user_address,
                timestamp=datetime.utcnow().timestamp(),
                collaterals=[
                    Collateral(
                        protocol=ProtocolName.aave,
                        asset="various",
                        amount=total_collateral_usd,
                        usd_value=total_collateral_usd,
                    )
                ],
                borrowings=[
                    Borrowing(
                        protocol=ProtocolName.aave,
                        asset="various",
                        amount=total_debt_usd,
                        usd_value=total_debt_usd,
                        interest_rate=None,
                    )
                ],
                staked_positions=[],
                health_scores=[
                    HealthScore(
                        protocol=ProtocolName.aave,
                        score=health_factor / AAVE_DECIMALS,
                    )
                ],
            )
        except Exception:
            logging.warning(
                "Could not fetch Aave snapshot for %s",
                user_address,
                exc_info=True,
            )
            return None
