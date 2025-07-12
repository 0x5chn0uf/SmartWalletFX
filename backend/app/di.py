"""Simple DI helpers for non-FastAPI contexts (e.g. Celery)."""

from sqlalchemy.orm import Session

from app.core.database import SyncSessionLocal


def get_session_sync() -> Session:  # pragma: no cover
    """Return a new synchronous SQLAlchemy Session."""
    return SyncSessionLocal()
