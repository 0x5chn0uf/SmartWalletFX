"""Simple DI helpers for non-FastAPI contexts (e.g. Celery)."""

from sqlalchemy.orm import Session

from app.core.services import ServiceContainer
from app.services.snapshot_aggregation import SnapshotAggregationService
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioAggregationUsecase,
)


def get_session_sync(container: ServiceContainer) -> Session:  # pragma: no cover
    """Return a new synchronous SQLAlchemy ``Session``.

    Parameters
    ----------
    container:
        :class:`ServiceContainer` to draw the database service from.
    """

    return container.db.SyncSessionLocal()


def get_snapshot_service_sync(
    *, container: ServiceContainer
) -> SnapshotAggregationService:  # pragma: no cover
    """Return :class:`SnapshotAggregationService` wired with a sync session."""

    session = get_session_sync(container)
    return SnapshotAggregationService(session, _build_aggregator())


# ---------------------------------------------------------------------------
# Adapter factory helpers
# ---------------------------------------------------------------------------


def _build_aggregator():
    """Create an aggregation callable bound to default adapters list."""

    usecase = PortfolioAggregationUsecase()

    async def _aggregator(address: str):  # type: ignore[override]
        return await usecase.aggregate_portfolio_metrics(address)

    return _aggregator
