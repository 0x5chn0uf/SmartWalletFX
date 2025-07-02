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
import sqlalchemy as _sa

import app.core.database as db_mod
from app.models import Base


def _make_test_db(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
    """Return (async_url, sync_url) for a fresh test database.

    The implementation supports two backends:

    1. **SQLite (default)** – Creates a temporary file-based DB under pytest's
       tmp_path_factory directory.  This mirrors the previous behaviour.

    2. **PostgreSQL** – When ``TEST_DB_URL`` is set *and* starts with
       ``postgresql``, we create a *brand-new* database (named with a random
       UUID) on the target server, then return connection strings pointing to
       it (async via ``+asyncpg`` and sync via psycopg2).
    """

    import os
    import uuid
    from sqlalchemy.engine.url import make_url, URL  # type: ignore

    env_url = os.getenv("TEST_DB_URL")

    # ------------------------------------------------------------------
    # Branch 1 – PostgreSQL.  We create a dedicated database so the test
    # session has an isolated schema and can freely ``DROP``/``CREATE``
    # tables without affecting other services (e.g. the dev database).
    # ------------------------------------------------------------------

    if env_url and env_url.startswith("postgresql"):
        url_obj = make_url(env_url)

        # Generate unique DB name to avoid collisions between concurrent runs
        test_db_name = f"test_{uuid.uuid4().hex}"

        # Build *admin* connection URL (connects to 'postgres' default DB)
        admin_url: URL = url_obj.set(database="postgres")

        # Use sync engine for DDL operations (CREATE DATABASE)
        admin_engine = create_engine(admin_url.render_as_string(hide_password=False))

        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            try:
                conn.execute(_sa.text(f"CREATE DATABASE {test_db_name}"))
            except Exception:  # pragma: no cover – DB already exists or race
                pass

        admin_engine.dispose()

        # Build async & sync URLs pointing to the *new* database
        async_url = url_obj.set(database=test_db_name).render_as_string(hide_password=False)

        if "+asyncpg" not in async_url:
            async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")

        sync_url = async_url.replace("+asyncpg", "")

        # Create tables inside the new database so individual tests don't
        # have to run migrations (keeps suite fast)
        temp_sync_engine = create_engine(sync_url)
        Base.metadata.create_all(bind=temp_sync_engine)
        temp_sync_engine.dispose()

        return async_url, sync_url

    # ------------------------------------------------------------------
    # Branch 2 – SQLite (fallback)
    # ------------------------------------------------------------------

    db_dir = tmp_path_factory.mktemp("db")
    db_file = db_dir / "test.sqlite"
    async_url = f"sqlite+aiosqlite:///{db_file}"
    sync_url = f"sqlite:///{db_file}"

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
        # Dispose connections first so Postgres allows DROP DATABASE
        await engine.dispose()

        # Automatic cleanup for PostgreSQL databases created in _make_test_db
        env_url = os.getenv("TEST_DB_URL")

        if env_url and env_url.startswith("postgresql"):
            from sqlalchemy.engine.url import make_url, URL  # type: ignore

            url_obj = make_url(env_url)
            test_db_name = url_obj.database

            # Connect to admin database to DROP the temporary one
            admin_url: URL = url_obj.set(database="postgres")
            admin_engine = create_engine(
                admin_url.render_as_string(hide_password=False)
            )

            with admin_engine.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as conn:
                try:
                    conn.execute(_sa.text(f"DROP DATABASE IF EXISTS {test_db_name} WITH (FORCE)"))
                except Exception:  # pragma: no cover – best-effort cleanup
                    pass

            admin_engine.dispose()


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
