"""FastAPI dependency providers for reusable services."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3

from app.core.database import get_db
from app.core.config import settings
from app.services.snapshot_aggregation import SnapshotAggregationService
from app.usecase.defi_aave_usecase import AaveUsecase
from app.usecase.defi_compound_usecase import CompoundUsecase
from app.usecase.defi_radiant_usecase import RadiantUsecase
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioAggregationUsecase,
)
from app.usecase.portfolio_snapshot_usecase import PortfolioSnapshotUsecase


def _build_aggregator_async():
    usecase = PortfolioAggregationUsecase()

    async def _aggregator(address: str):  # type: ignore[override]
        return await usecase.aggregate_portfolio_metrics(address)

    return _aggregator


def get_snapshot_service(
    db: AsyncSession = Depends(get_db),
) -> SnapshotAggregationService:  # pragma: no cover – simple factory
    """Provide a SnapshotAggregationService with an injected async session."""
    return SnapshotAggregationService(db, _build_aggregator_async())


# --- Blockchain Provider ---


@lru_cache()
def get_w3():
    uri = getattr(
        settings, "WEB3_PROVIDER_URI", "https://ethereum-rpc.publicnode.com"
    )
    return Web3(Web3.HTTPProvider(uri))


# --- Usecase Dependencies ---


def get_aave_usecase(w3: Web3 = Depends(get_w3)) -> AaveUsecase:
    return AaveUsecase(w3)


def get_compound_usecase(w3: Web3 = Depends(get_w3)) -> CompoundUsecase:
    return CompoundUsecase(w3)


def get_radiant_usecase() -> RadiantUsecase:
    return RadiantUsecase()


def get_portfolio_aggregation_usecase() -> PortfolioAggregationUsecase:
    return PortfolioAggregationUsecase()
