# flake8: noqa

import asyncio
import datetime
import os
import pathlib
import subprocess
import sys
import time
from contextlib import AsyncExitStack, asynccontextmanager

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text  # sync version
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

# Ensure repository root (backend/) is on PYTHONPATH so that 'import app' works
BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


import app.core.database as db_mod
from app.core.database import get_db
from app.main import create_app
from app.models import Base
from app.usecase.portfolio_aggregation_usecase import PortfolioMetrics

# Use a file-based SQLite DB for all tests
TEST_DB_PATH = "./smartwallet_test.db"
TEST_DB_URL = "sqlite+aiosqlite:///./smartwallet_test.db"
ALEMBIC_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../alembic.ini")
)

# Run Alembic migrations in a subprocess before any tests start


@asynccontextmanager
async def async_test_engine(db_url: str):
    """
    Reusable async context manager for test engines.
    Provides proper engine lifecycle management with AsyncExitStack.

    Usage:
        async with async_test_engine("sqlite+aiosqlite:///:memory:") as engine:
            # Use engine for tests
            pass
        # Engine is automatically disposed
    """
    async with AsyncExitStack() as stack:
        engine = create_async_engine(db_url, future=True)
        stack.push_async_callback(engine.dispose)
        yield engine


def pytest_sessionstart(session):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    env = os.environ.copy()
    env["TEST_DB_URL"] = "sqlite:///./smartwallet_test.db"
    subprocess.run(
        ["alembic", "-c", ALEMBIC_CONFIG_PATH, "upgrade", "head"],
        check=True,
        env=env,
    )
    time.sleep(0.1)  # Ensure file is flushed


def pytest_sessionfinish(session, exitstatus):
    """Clean up test database file after all tests complete."""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """
    Function-scoped async engine fixture using AsyncExitStack for proper teardown.
    Ensures engine disposal happens in the correct async context.
    """
    async with AsyncExitStack() as stack:
        engine = create_async_engine(TEST_DB_URL, future=True)
        # Register engine for automatic disposal
        stack.push_async_callback(engine.dispose)
        yield engine
        # AsyncExitStack handles disposal automatically in correct order


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
    """Return the *singleton* FastAPI application for tests.

    We reuse the instance created at import time in *app.main* to avoid the
    costly FastAPI *startup* sequence (and its SQL ``CREATE TABLE`` calls)
    multiple times. Only the database engine/session bindings are patched to
    use the per-session *async_engine* fixture.
    """

    # Patch engine and SessionLocal globally for the application
    db_mod.engine = async_engine
    db_mod.SessionLocal = async_sessionmaker(
        bind=db_mod.engine, class_=AsyncSession, expire_on_commit=False
    )

    # Reuse existing app instance instead of creating a new one each time
    from app.main import app as _app

    yield _app


@pytest.fixture(autouse=True)
def clean_db():
    yield  # Run test first

    sync_url = "sqlite:///./smartwallet_test.db"
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


# --------------------------------------------------------------------
# Refactored Fixtures
# --------------------------------------------------------------------


@pytest.fixture(scope="module")
def sync_session():
    """Create a synchronous, in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    yield db_session
    db_session.close()


@pytest.fixture(autouse=True, scope="module")
def patch_sync_db():
    """Patches the sync db engine and session for Celery tasks."""
    import app.core.database as db_mod
    import app.tasks.snapshots as snapshots_mod

    sync_url = "sqlite:///./smartwallet_test.db"
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False})
    SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    db_mod.sync_engine = sync_engine
    db_mod.SyncSessionLocal = SyncSessionLocal
    snapshots_mod.SyncSessionLocal = SyncSessionLocal
    yield


@pytest.fixture
def mock_settings(monkeypatch):
    """Mocks the ARBITRUM_RPC_URL setting."""
    monkeypatch.setattr("app.core.config.settings.ARBITRUM_RPC_URL", "http://mock-rpc")


@pytest.fixture()
def dummy_metrics():
    """Returns a dummy PortfolioMetrics object."""
    return PortfolioMetrics.model_construct(
        user_address="0xabc",
        total_collateral=1.0,
        total_borrowings=0.5,
        total_collateral_usd=1.0,
        total_borrowings_usd=0.5,
        aggregate_health_score=None,
        aggregate_apy=None,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
        historical_snapshots=None,
        timestamp=datetime.datetime.utcnow(),
    )


@pytest.fixture(autouse=True)
def override_get_db(db_session):
    """Fixture to override the 'get_db' dependency in the FastAPI app."""

    async def _override():
        yield db_session

    from app.main import app

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


# --------------------------------------------------------------------
# AnyIO backend override – restrict to asyncio only to avoid trio issues
# --------------------------------------------------------------------


@pytest.fixture(scope="session")
def anyio_backend():
    """Force AnyIO to use only the asyncio backend during tests."""
    return "asyncio"
