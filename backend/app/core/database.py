# Synchronous SQLAlchemy imports for Celery / legacy callers
"""Database helpers relying on :class:`ServiceContainer`."""

from app.core.services import ServiceContainer

# Default service container used by modules that import from ``app.core.database``.
# Applications are expected to create and pass their own container instance.
container = ServiceContainer(load_celery=False)

# Shared SQLAlchemy ``Base`` used by model declarations
Base = container.db.Base


async def get_db():
    """Yield a new async database session using the default container."""

    async for session in container.db.get_db():
        yield session
