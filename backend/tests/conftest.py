import asyncio
import os
import subprocess
import time

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text  # sync version
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.core.database as db_mod
from app.main import create_app

# Use a file-based SQLite DB for all tests
TEST_DB_PATH = "./test.db"
TEST_DB_URL = "sqlite+aiosqlite:///./test.db"
ALEMBIC_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../alembic.ini")
)

# Run Alembic migrations in a subprocess before any tests start


def pytest_sessionstart(session):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    subprocess.run(
        ["alembic", "-c", ALEMBIC_CONFIG_PATH, "upgrade", "head"], check=True
    )
    time.sleep(0.1)  # Ensure file is flushed


@pytest.fixture(scope="session")
def async_engine():
    engine = create_async_engine(TEST_DB_URL, future=True)
    yield engine
    asyncio.get_event_loop().run_until_complete(engine.dispose())
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture
async def db_session(async_engine):
    async_session = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


@pytest_asyncio.fixture
async def test_app(async_engine):
    # Patch engine and SessionLocal globally for the app
    db_mod.engine = async_engine
    db_mod.SessionLocal = async_sessionmaker(
        bind=db_mod.engine, class_=AsyncSession, expire_on_commit=False
    )

    app = create_app()
    yield app


@pytest.fixture(autouse=True)
def clean_db():
    yield  # Run test first

    sync_url = "sqlite:///./test.db"
    engine = create_engine(sync_url)
    conn = engine.connect()
    trans = conn.begin()
    inspector = inspect(engine)

    for table in inspector.get_table_names():
        if table != "alembic_version":
            conn.execute(text(f"DELETE FROM {table}"))
    trans.commit()

    conn.close()
    engine.dispose()
