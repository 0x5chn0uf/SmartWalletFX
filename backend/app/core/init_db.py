from app.core.database import Base, DatabaseService


async def init_db(database_service: DatabaseService) -> None:
    """
    Initialize the database tables asynchronously.
    Creates all tables defined in the SQLAlchemy models if they do not exist.
    """
    async with database_service.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
