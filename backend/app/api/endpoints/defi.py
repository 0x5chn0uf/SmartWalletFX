from fastapi import APIRouter, HTTPException

from app.schemas.defi import DeFiAccountSnapshot
from app.usecase.defi_aave_usecase import get_aave_user_snapshot_usecase
from app.usecase.defi_compound_usecase import (
    get_compound_user_snapshot_usecase,
)
from app.usecase.defi_radiant_usecase import get_radiant_user_snapshot_usecase
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioMetrics,
    aggregate_portfolio_metrics,
)

router = APIRouter()


@router.get(
    "/defi/radiant/{address}",
    response_model=DeFiAccountSnapshot,
    tags=["DeFi"],
)
async def get_radiant_user_data(address: str):
    """
    Get Radiant user data for a given wallet address (Arbitrum network).
    Returns the user's DeFi account snapshot (collateral, borrowings,
    health score, etc.) by querying the Radiant smart contract directly.
    """
    snapshot = await get_radiant_user_snapshot_usecase(address)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=("User data not found on Radiant smart contract."),
        )
    return snapshot


@router.get(
    "/defi/aave/{address}",
    response_model=DeFiAccountSnapshot,
    tags=["DeFi"],
)
async def get_aave_user_data(address: str):
    """
    Get Aave user data for a given wallet address (Ethereum mainnet).
    Returns the user's DeFi account snapshot (collateral, borrowings,
    health score, etc.).
    """
    snapshot = await get_aave_user_snapshot_usecase(address)
    if snapshot is None:
        raise HTTPException(
            status_code=404, detail="User data not found on Aave subgraph."
        )
    return snapshot


@router.get(
    "/defi/compound/{address}",
    response_model=DeFiAccountSnapshot,
    tags=["DeFi"],
)
async def get_compound_user_data(address: str):
    """
    Get Compound user data for a given wallet address (Ethereum mainnet).
    Returns the user's DeFi account snapshot (collateral,
    borrowings, health score, etc.).
    """
    snapshot = await get_compound_user_snapshot_usecase(address)
    if snapshot is None:
        raise HTTPException(
            status_code=404, detail="User data not found on Compound subgraph."
        )
    return snapshot


@router.get(
    "/defi/portfolio/{address}",
    response_model=PortfolioMetrics,
    tags=["DeFi"],
)
async def get_portfolio_metrics(address: str):
    """
    Get aggregated portfolio metrics for a given wallet address across
    all supported DeFi protocols.
    Returns total collateral, total borrowings, aggregate health score,
    aggregate APY, and all positions.
    """
    return await aggregate_portfolio_metrics(address)
