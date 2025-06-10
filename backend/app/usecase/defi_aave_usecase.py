"""
Aave DeFi Use Case Logic

This module provides the use case for fetching and mapping Aave user data
from the subgraph (Ethereum mainnet). It exposes a function to retrieve
a DeFiAccountSnapshot for a given address, using the agnostic backend models.
"""
from typing import Optional

import httpx

from app.schemas.defi import (
    Borrowing,
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
    StakedPosition,
)

SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/aave/protocol-v2"


async def get_aave_user_snapshot_usecase(
    user_address: str,
) -> Optional[DeFiAccountSnapshot]:
    """
    Fetch and aggregate all Aave data for a given user address using the
    subgraph.
    Maps the subgraph response to the agnostic DeFiAccountSnapshot model.
    Args:
        user_address (str): The user's wallet address.
    Returns:
        Optional[DeFiAccountSnapshot]: Aggregated Aave data for the user,
        or None if not found.
    """
    query = """
    query getUserData($user: String!) {
      userReserves(where: {user: $user}) {
        reserve {
          symbol
          decimals
          liquidityRate
          variableBorrowRate
        }
        scaledATokenBalance
        currentTotalDebt
      }
      userAccountData(id: $user) {
        healthFactor
        totalCollateralETH
        totalDebtETH
      }
    }
    """
    variables = {"user": user_address.lower()}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SUBGRAPH_URL, json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        data = response.json()
    reserves = data.get("data", {}).get("userReserves", [])
    account_data = data.get("data", {}).get("userAccountData")
    if not reserves and not account_data:
        return None
    collaterals = []
    borrowings = []
    staked_positions = []
    for reserve in reserves:
        symbol = reserve["reserve"]["symbol"]
        decimals = int(reserve["reserve"].get("decimals", 18))
        liquidity_rate = (
            float(reserve["reserve"].get("liquidityRate", 0)) / 1e27
            if reserve["reserve"].get("liquidityRate")
            else None
        )
        variable_borrow_rate = (
            float(reserve["reserve"].get("variableBorrowRate", 0)) / 1e27
            if reserve["reserve"].get("variableBorrowRate")
            else None
        )
        scaled_balance = float(reserve.get("scaledATokenBalance", 0)) / (
            10**decimals
        )
        total_debt = float(reserve.get("currentTotalDebt", 0)) / (
            10**decimals
        )
        if scaled_balance > 0:
            collaterals.append(
                Collateral(
                    protocol=ProtocolName.aave,
                    asset=symbol,
                    amount=scaled_balance,
                    usd_value=0,
                )
            )
            if liquidity_rate:
                staked_positions.append(
                    StakedPosition(
                        protocol=ProtocolName.aave,
                        asset=symbol,
                        amount=scaled_balance,
                        usd_value=0,
                        apy=liquidity_rate,
                    )
                )
        if total_debt > 0:
            borrowings.append(
                Borrowing(
                    protocol=ProtocolName.aave,
                    asset=symbol,
                    amount=total_debt,
                    usd_value=0,
                    interest_rate=variable_borrow_rate,
                )
            )
    health_scores = []
    if account_data and account_data.get("healthFactor") is not None:
        try:
            score = float(account_data["healthFactor"]) / 1e18
            health_scores.append(
                HealthScore(protocol=ProtocolName.aave, score=score)
            )
        except Exception:
            pass
    snapshot = DeFiAccountSnapshot(
        user_address=user_address,
        timestamp=0,  # Should be set to current or block timestamp
        # if available
        collaterals=collaterals,
        borrowings=borrowings,
        staked_positions=staked_positions,
        health_scores=health_scores,
        total_apy=None,
    )
    return snapshot
