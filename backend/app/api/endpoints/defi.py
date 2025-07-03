# flake8: noqa

import re
import time
from datetime import datetime
from enum import Enum
from typing import List, Union

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import auth_deps
from app.api.dependencies import blockchain_deps as deps
from app.celery_app import celery
from app.core.database import get_db
from app.repositories.portfolio_snapshot_repository import (
    PortfolioSnapshotRepository,
)
from app.schemas.defi import DeFiAccountSnapshot, PortfolioSnapshot
from app.schemas.defi_aggregate import AggregateMetricsSchema, PositionSchema
from app.schemas.defi_dashboard import DefiKPI, ProtocolBreakdown
from app.schemas.portfolio_timeline import TimelineResponse
from app.services.defi_aggregation_service import DeFiAggregationService
from app.usecase.defi_aave_usecase import AaveUsecase
from app.usecase.defi_compound_usecase import CompoundUsecase
from app.usecase.defi_radiant_usecase import RadiantUsecase
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioAggregationUsecase,
    PortfolioMetrics,
)
from app.usecase.portfolio_snapshot_usecase import PortfolioSnapshotUsecase

logger = structlog.get_logger(__name__)

router = APIRouter()


# --- Dashboard Endpoints (Mocked) ---

MOCK_PROTOCOLS: List[ProtocolBreakdown] = [
    ProtocolBreakdown(name="Aave", tvl=534221.12, apy=1.2, positions=10),
    ProtocolBreakdown(name="Compound", tvl=312876.44, apy=9.1, positions=2),
    ProtocolBreakdown(name="Radiant", tvl=407224.89, apy=20.2, positions=5),
]

MOCK_PORTFOLIO_TIMELINE = {
    "snapshots": [
        {
            "user_address": "0xMOCK",
            "timestamp": 1719446400,
            "total_collateral": 1200000,
            "total_borrowings": 0,
            "aggregate_health_score": None,
        },
        {
            "user_address": "0xMOCK",
            "timestamp": 1719532800,
            "total_collateral": 1225000,
            "total_borrowings": 0,
            "aggregate_health_score": None,
        },
        {
            "user_address": "0xMOCK",
            "timestamp": 1719619200,
            "total_collateral": 1210000,
            "total_borrowings": 0,
            "aggregate_health_score": None,
        },
    ],
    "interval": "1d",
    "limit": 3,
    "offset": 0,
    "total": 3,
}


@router.get("/defi/portfolio/kpi", response_model=DefiKPI, tags=["DeFi"])
async def get_defi_kpi():
    """Return basic KPI metrics for the DeFi dashboard (mock placeholder)."""
    total_tvl = sum(p.tvl for p in MOCK_PROTOCOLS)
    avg_apy = round(sum(p.apy for p in MOCK_PROTOCOLS) / len(MOCK_PROTOCOLS), 2)
    return DefiKPI(
        tvl=total_tvl,
        apy=avg_apy,
        protocols=MOCK_PROTOCOLS,
        updated_at=datetime.utcnow(),
    )


@router.get(
    "/defi/portfolio/protocols", response_model=List[ProtocolBreakdown], tags=["DeFi"]
)
async def get_protocol_breakdown():
    """Return protocol-level breakdown for dashboard table (mock placeholder)."""
    return MOCK_PROTOCOLS


# Database dependency
db_dependency = Depends(get_db)

# Ethereum address validation pattern
ETH_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")


def validate_ethereum_address(address: str) -> str:
    """Validate that the address is a valid Ethereum address."""
    if not ETH_ADDRESS_PATTERN.match(address):
        raise HTTPException(
            status_code=422,
            detail="Invalid Ethereum address format. Must be a 42-character hex string starting with 0x.",
        )
    return address.lower()


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
    request: Request,
    address: str,
    usecase: RadiantUsecase = Depends(deps.get_radiant_usecase),
):
    """
    Get Radiant user data for a given wallet address (Arbitrum network).
    Returns the user's DeFi account snapshot (collateral, borrowings,
    health score, etc.) by querying the Radiant smart contract directly.
    """
    start_time = time.time()
    client_ip = request.client.host or "unknown"

    logger.info(
        "Radiant user data request started", address=address, client_ip=client_ip
    )

    try:
        snapshot = await usecase.get_user_snapshot(address)
        if snapshot is None:
            duration = int((time.time() - start_time) * 1000)
            logger.warning(
                "Radiant user data not found",
                address=address,
                client_ip=client_ip,
                duration_ms=duration,
            )
            raise HTTPException(
                status_code=404,
                detail=("User data not found on Radiant smart contract."),
            )

        duration = int((time.time() - start_time) * 1000)
        logger.info(
            "Radiant user data retrieved successfully",
            address=address,
            client_ip=client_ip,
            duration_ms=duration,
        )

        return snapshot
    except HTTPException:
        raise
    except Exception as exc:
        duration = int((time.time() - start_time) * 1000)
        logger.error(
            "Radiant user data request failed",
            address=address,
            client_ip=client_ip,
            duration_ms=duration,
            error=str(exc),
            exc_info=True,
        )
        raise


@router.get(
    "/defi/aave/{address}",
    response_model=DeFiAccountSnapshot,
    tags=["DeFi"],
)
async def get_aave_user_data(
    request: Request,
    address: str,
    usecase: AaveUsecase = Depends(deps.get_aave_usecase),
):
    """
    Get Aave user data for a given wallet address (Ethereum mainnet).
    Returns the user's DeFi account snapshot (collateral, borrowings,
    health score, etc.).
    """
    start_time = time.time()
    client_ip = request.client.host or "unknown"

    logger.info("Aave user data request started", address=address, client_ip=client_ip)

    try:
        snapshot = await usecase.get_user_snapshot(address)
        if snapshot is None:
            duration = int((time.time() - start_time) * 1000)
            logger.warning(
                "Aave user data not found",
                address=address,
                client_ip=client_ip,
                duration_ms=duration,
            )
            raise HTTPException(status_code=404, detail="User data not found on Aave.")

        duration = int((time.time() - start_time) * 1000)
        logger.info(
            "Aave user data retrieved successfully",
            address=address,
            client_ip=client_ip,
            duration_ms=duration,
        )

        return snapshot
    except HTTPException:
        raise
    except Exception as exc:
        duration = int((time.time() - start_time) * 1000)
        logger.error(
            "Aave user data request failed",
            address=address,
            client_ip=client_ip,
            duration_ms=duration,
            error=str(exc),
            exc_info=True,
        )
        raise


@router.get(
    "/defi/compound/{address}",
    response_model=DeFiAccountSnapshot,
    tags=["DeFi"],
)
async def get_compound_user_data(
    address: str, usecase: CompoundUsecase = Depends(deps.get_compound_usecase)
):
    """
    Get Compound user data for a given wallet address (Ethereum mainnet).
    Returns the user's DeFi account snapshot (collateral, borrowings).
    """
    snapshot = await usecase.get_user_snapshot(address)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="User data not found on Compound.")
    return snapshot


@router.get("/defi/portfolio/timeline", response_model=TimelineResponse, tags=["DeFi"])
async def get_main_portfolio_timeline():
    """Return a timeline for the main portfolio view (mock placeholder)."""
    return MOCK_PORTFOLIO_TIMELINE


@router.get(
    "/defi/portfolio/{address}",
    response_model=PortfolioMetrics,
    tags=["DeFi"],
)
async def get_portfolio_metrics(
    address: str,
    usecase: PortfolioAggregationUsecase = Depends(
        deps.get_portfolio_aggregation_usecase
    ),
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
    repository = PortfolioSnapshotRepository(db)
    return PortfolioSnapshotUsecase(repository)


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


@router.get("/defi/health", tags=["DeFi"])
async def defi_health_check():
    """Lightweight health check for DeFi component."""
    return {"status": "ok"}


@router.get(
    "/defi/aggregate/{address}",
    response_model=AggregateMetricsSchema,
    tags=["DeFi"],
    dependencies=[Depends(auth_deps.get_current_user)],
)
async def get_aggregate_metrics(
    address: str,
    db: AsyncSession = db_dependency,
):
    """Return aggregated multi-protocol metrics for *address* with caching."""

    # Validate Ethereum address format
    validated_address = validate_ethereum_address(address)

    # Create service instance
    aggregation_service = DeFiAggregationService(db)

    # Validate address using service method
    if not aggregation_service.validate_ethereum_address(validated_address):
        raise HTTPException(
            status_code=422,
            detail="Invalid Ethereum address format. Must be a 42-character hex string starting with 0x.",
        )

    # Aggregate positions using the service
    metrics = await aggregation_service.aggregate_wallet_positions(validated_address)

    # Convert to schema for API response
    schema = AggregateMetricsSchema(
        id=str(metrics.id),
        wallet_id=metrics.wallet_id,
        tvl=metrics.tvl,
        total_borrowings=metrics.total_borrowings,
        aggregate_apy=metrics.aggregate_apy,
        as_of=metrics.as_of,
        positions=[
            PositionSchema(
                protocol=p.get("protocol", "unknown"),
                asset=p.get("asset", "unknown"),
                amount=p.get("amount", 0.0),
                usd_value=p.get("usd_value", 0.0),
                apy=p.get("apy"),
            )
            for p in metrics.positions
        ],
    )

    return schema
