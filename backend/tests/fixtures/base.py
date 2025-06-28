"""Base fixtures for the test suite."""

import os
import pathlib

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

import app.core.database as db_mod
from app.models import Base


def _make_test_db(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
    """Return (async_url, sync_url) for a fresh SQLite file under tmp dir."""
    db_dir = tmp_path_factory.mktemp("db")
    db_file = db_dir / "test.sqlite"
    async_url = f"sqlite+aiosqlite:///{db_file}"
    sync_url = f"sqlite:///{db_file}"

    # Create a temporary engine for this specific DB file
    temp_engine = create_engine(sync_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=temp_engine)
    temp_engine.dispose()

    return async_url, sync_url


@pytest_asyncio.fixture(scope="session")
async def async_engine(tmp_path_factory: pytest.TempPathFactory):
    """Yield a *brand-new* AsyncEngine bound to a fresh SQLite file."""

    async_url, sync_url = _make_test_db(tmp_path_factory)

    # Expose to other fixtures (patch_sync_db) via environment variable
    os.environ["TEST_DB_URL"] = sync_url

    engine = create_async_engine(async_url, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="session")
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

    # Also patch the sync engine to use the same test database
    from sqlalchemy import create_engine

    sync_url = os.environ["TEST_DB_URL"]
    db_mod.sync_engine = create_engine(
        sync_url, connect_args={"check_same_thread": False}
    )
    db_mod.SyncSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_mod.sync_engine
    )

    # Reuse existing app instance instead of creating a new one each time
    from app.main import app as _app

    yield _app
