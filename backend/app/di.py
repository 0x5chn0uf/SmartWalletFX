"""Simple DI helpers for non-FastAPI contexts (e.g. Celery)."""

from sqlalchemy.orm import Session

from app.core.database import SyncSessionLocal
from app.services.snapshot_aggregation import SnapshotAggregationService


def get_session_sync() -> Session:  # pragma: no cover
    """Return a new synchronous SQLAlchemy Session."""
    return SyncSessionLocal()


def get_snapshot_service_sync() -> SnapshotAggregationService:  # pragma: no cover
    """Return SnapshotAggregationService wired with a sync session."""
    return SnapshotAggregationService(get_session_sync()) 