"""FastAPI dependency providers for reusable services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.snapshot_aggregation import SnapshotAggregationService


def get_snapshot_service(
    db: AsyncSession = Depends(get_db),
) -> SnapshotAggregationService:  # pragma: no cover – simple factory
    """Provide a SnapshotAggregationService with an injected async session."""
    return SnapshotAggregationService(db) 