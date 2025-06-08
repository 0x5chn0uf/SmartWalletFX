# import asyncio

from app.core.database import Base, engine


async def init_db() -> None:
    """
    Initialize the database tables asynchronously.
    Creates all tables defined in the SQLAlchemy models if they do not exist.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
