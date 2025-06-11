from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.defi import DeFiAccountSnapshot, PortfolioSnapshot
from app.stores.portfolio_snapshot_store import PortfolioSnapshotStore
from app.usecase.defi_aave_usecase import get_aave_user_snapshot_usecase
from app.usecase.defi_compound_usecase import (
    get_compound_user_snapshot_usecase,
)
from app.usecase.defi_radiant_usecase import get_radiant_user_snapshot_usecase
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioMetrics,
    aggregate_portfolio_metrics,
)
from app.usecase.portfolio_snapshot_usecase import PortfolioSnapshotUsecase

router = APIRouter()

db_dependency = Depends(get_db)


class IntervalEnum(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


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


async def get_portfolio_snapshot_usecase(db: AsyncSession):
    store = PortfolioSnapshotStore(db)
    return PortfolioSnapshotUsecase(store)


@router.get(
    "/defi/timeline/{address}",
    response_model=List[PortfolioSnapshot],
    tags=["DeFi"],
)
async def get_portfolio_timeline(
    address: str,
    from_ts: int = Query(
        ..., description="Start of time range (unix timestamp)"
    ),
    to_ts: int = Query(..., description="End of time range (unix timestamp)"),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="""
            Max number of snapshots to return (default 100, max 1000)
        """,
    ),
    offset: int = Query(
        0, ge=0, description="Number of snapshots to skip (default 0)"
    ),
    interval: IntervalEnum = Query(
        IntervalEnum.NONE,
        description="Aggregation interval: none, daily, weekly",
    ),
    db: AsyncSession = db_dependency,
):
    """
    Get historical portfolio snapshots (timeline) for a given wallet
    address and time range.
    Returns a list of PortfolioSnapshot objects for charting and analysis.
    Supports pagination with 'limit' and 'offset' query parameters.
    Supports interval aggregation with 'interval' (none, daily, weekly).
    """
    usecase = await get_portfolio_snapshot_usecase(db)
    return await usecase.get_timeline(
        address,
        from_ts,
        to_ts,
        limit=limit,
        offset=offset,
        interval=interval.value,
    )
