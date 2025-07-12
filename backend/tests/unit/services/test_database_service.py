import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.services import DatabaseService
from app.models import Base


@pytest.mark.asyncio
async def test_database_service_provides_async_and_sync_sessions(tmp_path):
    db_file = tmp_path / "test.db"
    settings = Settings(DATABASE_URL=f"sqlite+aiosqlite:///{db_file}")
    service = DatabaseService(settings)

    # Create tables
    async with service.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with service.async_session_factory() as session:
        assert isinstance(session, AsyncSession)
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1

    with service.sync_session_factory() as session:
        result = session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
