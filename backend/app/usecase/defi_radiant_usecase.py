"""
Radiant DeFi Use Case Logic

This module provides the use case for fetching and mapping Radiant user data
from the smart contract (Arbitrum network). It exposes a function to retrieve
a DeFiAccountSnapshot for a given address, using the agnostic backend models.
"""
import time
from typing import Optional

from app.adapters.radiant_contract_adapter import (
    RadiantAdapterError,
    RadiantContractAdapter,
)
from app.schemas.defi import (
    Borrowing,
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
)

_adapter = RadiantContractAdapter()


async def get_radiant_user_snapshot_usecase(
    user_address: str,
) -> Optional[DeFiAccountSnapshot]:
    """
    Fetch and aggregate all Radiant data for a given user address using the
    smart contract (web3.py).
    Maps the contract response to the agnostic DeFiAccountSnapshot model.
    Args:
        user_address (str): The user's wallet address.
    Returns:
        Optional[DeFiAccountSnapshot]: Aggregated Radiant data for the user,
        or None if not found.
    """
    try:
        data = await _adapter.async_get_user_data(user_address)
    except RadiantAdapterError:
        # Optionally log error
        return None
    if not data:
        return None
    reserves = data["reserves"]
    health_factor = data.get("health_factor")
    collaterals = []
    borrowings = []
    for r in reserves:
        asset = r["token_address"]
        decimals = r.get("decimals", 18)
        supplied = float(r["supplied"]) / (10**decimals)
        supplied_usd = float(r.get("supplied_usd", 0))
        used_as_collateral = bool(r["used_as_collateral"])
        variable_borrowed = float(r.get("variable_borrowed", 0)) / (
            10**decimals
        )
        stable_borrowed = float(r.get("stable_borrowed", 0)) / (10**decimals)
        if supplied > 0 and used_as_collateral:
            collaterals.append(
                Collateral(
                    protocol=ProtocolName.radiant,
                    asset=asset,
                    amount=supplied,
                    usd_value=supplied_usd,
                )
            )
        if variable_borrowed > 0:
            borrowings.append(
                Borrowing(
                    protocol=ProtocolName.radiant,
                    asset=asset,
                    amount=variable_borrowed,
                    usd_value=0,  # TODO: fetch price
                    interest_rate=None,  # TODO: fetch rate
                )
            )
        if stable_borrowed > 0:
            borrowings.append(
                Borrowing(
                    protocol=ProtocolName.radiant,
                    asset=asset,
                    amount=stable_borrowed,
                    usd_value=0,  # TODO: fetch price
                    interest_rate=None,  # TODO: fetch rate
                )
            )
    health_scores = []
    if health_factor is not None:
        try:
            score = float(health_factor)
            health_scores.append(
                HealthScore(protocol=ProtocolName.radiant, score=score)
            )
        except Exception:
            pass
    snapshot = DeFiAccountSnapshot(
        user_address=user_address,
        timestamp=int(time.time()),
        collaterals=collaterals,
        borrowings=borrowings,
        staked_positions=[],
        health_scores=health_scores,
        total_apy=None,
    )
    return snapshot
