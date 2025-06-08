import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.core.database as db_mod
from app.core.database import Base
from app.core.init_db import init_db
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


@pytest_asyncio.fixture
async def db_session(request):
    db_url = getattr(request, "param", "sqlite+aiosqlite:///./test_db.db")
    engine = create_async_engine(
        db_url, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_app(db_session):
    # Patch engine and SessionLocal globally for the app
    db_mod.engine = db_session.bind
    db_mod.SessionLocal = async_sessionmaker(
        bind=db_mod.engine, class_=AsyncSession, expire_on_commit=False
    )
    # (Re)crée les tables pour l'app
    await init_db()
    app = create_app()
    yield app
