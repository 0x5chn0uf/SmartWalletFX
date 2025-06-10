"""
Compound DeFi Use Case Logic

This module provides the use case for fetching and mapping Compound
user data from the subgraph (Ethereum mainnet). It exposes a function
to retrieve a DeFiAccountSnapshot for a given address, using the agnostic
backend models.
"""
from typing import Optional

import httpx

from app.schemas.defi import (
    Borrowing,
    Collateral,
    DeFiAccountSnapshot,
    HealthScore,
    ProtocolName,
)

SUBGRAPH_URL = (
    "https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2"
)


async def get_compound_user_snapshot_usecase(
    user_address: str,
) -> Optional[DeFiAccountSnapshot]:
    """
    Fetch and aggregate all Compound data for a given user address using the
    subgraph. Maps the subgraph response to the agnostic DeFiAccountSnapshot
    model.
    Args:
        user_address (str): The user's wallet address.
    Returns:
        Optional[DeFiAccountSnapshot]: Aggregated Compound data for the user,
        or None if not found.
    """
    query = """
    query getAccount($id: ID!) {
      account(id: $id) {
        id
        health
        tokens {
          symbol
          supplyBalanceUnderlying
          borrowBalanceUnderlying
        }
      }
    }
    """
    variables = {"id": user_address.lower()}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SUBGRAPH_URL, json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        data = response.json()
    account = data.get("data", {}).get("account")
    if not account:
        return None
    collaterals = []
    borrowings = []
    staked_positions = []
    for token in account.get("tokens", []):
        symbol = token["symbol"]
        supply_balance = float(token.get("supplyBalanceUnderlying", 0))
        borrow_balance = float(token.get("borrowBalanceUnderlying", 0))
        if supply_balance > 0:
            collaterals.append(
                Collateral(
                    protocol=ProtocolName.compound,
                    asset=symbol,
                    amount=supply_balance,
                    usd_value=0,
                )
            )
        if borrow_balance > 0:
            borrowings.append(
                Borrowing(
                    protocol=ProtocolName.compound,
                    asset=symbol,
                    amount=borrow_balance,
                    usd_value=0,
                    interest_rate=None,
                )
            )
    health_scores = []
    if account.get("health") is not None:
        try:
            score = float(account["health"])
            health_scores.append(
                HealthScore(protocol=ProtocolName.compound, score=score)
            )
        except Exception:
            pass
    snapshot = DeFiAccountSnapshot(
        user_address=user_address,
        timestamp=0,  # Should be set to current or block
        # timestamp if available
        collaterals=collaterals,
        borrowings=borrowings,
        staked_positions=staked_positions,
        health_scores=health_scores,
        total_apy=None,
    )
    return snapshot
