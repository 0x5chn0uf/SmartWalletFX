# Synchronous SQLAlchemy imports for Celery / legacy callers
"""Database helpers using :class:`DatabaseService` under the hood."""


from app.core.services import ServiceContainer

# Default service container used by modules that import from app.core.database.
# Applications should instantiate their own container instead of relying on the
# module-level instance.  This global is kept for backward-compatibility.
container = ServiceContainer(load_celery=False)

# ---------------------------------------------------------------------------
# Expose commonly used attributes for compatibility with previous API
# ---------------------------------------------------------------------------
engine = container.db.engine
SessionLocal = container.db.SessionLocal
sync_engine = container.db.sync_engine
SyncSessionLocal = container.db.SyncSessionLocal
Base = container.db.Base


async def get_db():
    """Yield a new async database session using the default container."""

    async for session in container.db.get_db():
        yield session
