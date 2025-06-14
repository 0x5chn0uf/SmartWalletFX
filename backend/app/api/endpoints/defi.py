# flake8: noqa

from enum import Enum
from typing import Any, List, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3

from app.api.dependencies import (
    get_aave_usecase,
    get_compound_usecase,
    get_portfolio_aggregation_usecase,
    get_radiant_usecase,
)
from app.celery_app import celery
from app.core.database import get_db
from app.schemas.defi import DeFiAccountSnapshot, PortfolioSnapshot
from app.schemas.portfolio_timeline import TimelineResponse
from app.stores.portfolio_snapshot_store import PortfolioSnapshotStore
from app.usecase.defi_aave_usecase import AaveUsecase
from app.usecase.defi_compound_usecase import CompoundUsecase
from app.usecase.defi_radiant_usecase import RadiantUsecase
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioAggregationUsecase,
    PortfolioMetrics,
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
async def get_radiant_user_data(
    address: str, usecase: RadiantUsecase = Depends(get_radiant_usecase)
):
    """
    Get Radiant user data for a given wallet address (Arbitrum network).
    Returns the user's DeFi account snapshot (collateral, borrowings,
    health score, etc.) by querying the Radiant smart contract directly.
    """
    snapshot = await usecase.get_user_snapshot(address)
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
async def get_aave_user_data(
    address: str, usecase: AaveUsecase = Depends(get_aave_usecase)
):
    """
    Get Aave user data for a given wallet address (Ethereum mainnet).
    Returns the user's DeFi account snapshot (collateral, borrowings,
    health score, etc.).
    """
    snapshot = await usecase.get_user_snapshot(address)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="User data not found on Aave.")
    return snapshot


@router.get(
    "/defi/compound/{address}",
    response_model=DeFiAccountSnapshot,
    tags=["DeFi"],
)
async def get_compound_user_data(
    address: str, usecase: CompoundUsecase = Depends(get_compound_usecase)
):
    """
    Get Compound user data for a given wallet address (Ethereum mainnet).
    Returns the user's DeFi account snapshot (collateral, borrowings).
    """
    snapshot = await usecase.get_user_snapshot(address)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="User data not found on Compound.")
    return snapshot


@router.get(
    "/defi/portfolio/{address}",
    response_model=PortfolioMetrics,
    tags=["DeFi"],
)
async def get_portfolio_metrics(
    address: str,
    usecase: PortfolioAggregationUsecase = Depends(get_portfolio_aggregation_usecase),
):
    """
    Get aggregated portfolio metrics for a given wallet address across
    all supported DeFi protocols.
    Returns total collateral, total borrowings, aggregate health score,
    aggregate APY, and all positions.
    """
    return await usecase.aggregate_portfolio_metrics(address)


async def get_portfolio_snapshot_usecase(
    db: AsyncSession = db_dependency,
) -> PortfolioSnapshotUsecase:
    store = PortfolioSnapshotStore(db)
    return PortfolioSnapshotUsecase(store)


@router.get(
    "/defi/timeline/{address}",
    response_model=Union[TimelineResponse, List[PortfolioSnapshot]],
    tags=["DeFi"],
)
async def get_portfolio_timeline(
    address: str,
    from_ts: int = Query(
        ..., description="Start of time range (unix timestamp)"  # noqa: B008
    ),
    to_ts: int = Query(
        ..., description="End of time range (unix timestamp)"  # noqa: B008
    ),
    limit: int = Query(  # noqa: B008
        100,
        ge=1,
        le=1000,
        description="""
            Max number of snapshots to return (default 100, max 1000)
        """,
    ),
    offset: int = Query(  # noqa: B008
        0, ge=0, description="Number of snapshots to skip (default 0)"
    ),
    interval: IntervalEnum = Query(  # noqa: B008
        IntervalEnum.NONE,
        description="Aggregation interval: none, daily, weekly",
    ),
    raw: bool = Query(  # noqa: B008
        False, description="If true, return raw list without metadata."
    ),
    usecase: PortfolioSnapshotUsecase = Depends(get_portfolio_snapshot_usecase),
):
    """
    Get historical portfolio snapshots (timeline) for a given wallet
    address and time range.
    Returns a list of PortfolioSnapshot objects for charting and analysis.
    Supports pagination with 'limit' and 'offset' query parameters.
    Supports interval aggregation with 'interval' (none, daily, weekly).
    """
    snapshots = await usecase.get_timeline(
        address,
        from_ts,
        to_ts,
        limit=limit,
        offset=offset,
        interval=interval.value,
    )

    if raw:
        # Backward-compat raw response
        return TimelineResponse(  # type: ignore – FastAPI ignores extra
            snapshots=snapshots,
            interval=interval.value,
            limit=limit,
            offset=offset,
            total=len(snapshots),
        ).dict()[
            "snapshots"
        ]  # Returns list only

    return TimelineResponse(
        snapshots=snapshots,
        interval=interval.value,
        limit=limit,
        offset=offset,
        total=len(snapshots),
    )


@router.post(
    "/defi/admin/trigger-snapshot",
    tags=["Admin"],
    status_code=status.HTTP_200_OK,
)
def trigger_snapshot_collection():
    """Manually trigger the portfolio snapshot collection task."""
    task = celery.send_task("app.tasks.snapshots.collect_portfolio_snapshots")
    return {"status": "triggered", "task_id": task.id}
