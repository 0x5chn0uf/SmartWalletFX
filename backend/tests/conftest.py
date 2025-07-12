# flake8: noqa

import asyncio
import pathlib
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from hypothesis import settings

from app.core.database import get_db

from .fixtures.auth import *
from .fixtures.base import *
from .fixtures.client import *
from .fixtures.database import *
from .fixtures.mocks import *
from .fixtures.services import *
from .fixtures.test_data import *
from .fixtures.usecase import *

ALEMBIC_CONFIG_PATH = str(pathlib.Path(__file__).parent.parent / "alembic.ini")


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
# Hypothesis global configuration – keep tests fast & consistent
# --------------------------------------------------------------------

# Register a "fast" profile that limits examples and sets a reasonable deadline
# across the test suite unless individual tests override it explicitly.
settings.register_profile("fast", max_examples=25, deadline=timedelta(milliseconds=300))
settings.load_profile("fast")


def pytest_configure(config):  # noqa: D401
    """Pytest config hook.

    Note:
        We add a custom marker for performance tests which should be
        skipped during normal test runs.
    """
    config.addinivalue_line("markers", "performance: mark test as performance-related")


@pytest.fixture(scope="session")
def event_loop():  # noqa: D401 – pytest asyncio helper
    """Create a new event loop for the entire test session."""
    # Note:
    #   By default, pytest-asyncio creates a new event loop for each test
    #   function. We override this to use a single event loop for the whole
    #   session, which can improve performance.
    #   However, this requires careful test design to avoid state leakage
    #   between tests.
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# --------------------------------------------------------------------
# Legacy synchronous TestClient fixture
# --------------------------------------------------------------------


@pytest.fixture
def client(db_session: "AsyncSession", test_app):  # type: ignore[name-defined]
    """Return a synchronous TestClient bound to the test FastAPI app.

    Some older integration tests still rely on a *synchronous* `fastapi.TestClient`
    instead of the newer `httpx.AsyncClient`. We provide this thin compatibility
    layer so those tests keep working while the rest of the suite adopts the
    async client fixtures.
    """

    from app.core.database import get_db

    async def _override_get_db():
        yield db_session

    # Inject the overridden dependency so requests served by the TestClient
    # reuse the same *transactional* session provided by the db_session fixture.
    test_app.dependency_overrides[get_db] = _override_get_db

    with TestClient(test_app) as tc:
        yield tc

    # Clean up to avoid cross-test interference.
    test_app.dependency_overrides.pop(get_db, None)


# --------------------------------------------------------------------
# SQLite compatibility patches
# --------------------------------------------------------------------

# Our Alembic migrations define `server_default=sa.text("timezone('utc', now())")`
# for timestamp columns. When the unit-test suite runs against an **in-memory**
# SQLite database the `timezone` SQL function obviously does not exist which
# leads to ``OperationalError: unknown function: timezone`` at INSERT time.
#
# We register a *no-op* implementation so that SQLite simply returns the
# supplied timestamp unmodified.

import sqlalchemy as _sa


@_sa.event.listens_for(_sa.engine.Engine, "connect")
def _register_sqlite_timezone_function(dbapi_conn, connection_record):  # noqa: D401
    """Create a stub ``timezone(text, datetime)`` function for SQLite."""

    try:
        import sqlite3

        import aiosqlite

        if isinstance(dbapi_conn, sqlite3.Connection):
            dbapi_conn.create_function("timezone", 2, lambda tz, ts: ts)
        elif isinstance(dbapi_conn, aiosqlite.Connection):  # type: ignore[attr-defined]
            dbapi_conn.create_function("timezone", 2, lambda tz, ts: ts)
    except Exception:  # pragma: no cover – defensive safeguard
        # Fail silently – the function is best-effort; tests relying on
        # Postgres semantics should use a dedicated database fixture.
        pass


import pytest


@pytest.fixture(autouse=True)
def _patch_email_service(monkeypatch):
    """Disable outbound e-mails during the entire test session.

    Replaces *EmailService.send_email_verification* and *send_password_reset*
    with lightweight async no-ops so tests that register users or trigger
    password resets don't attempt real SMTP operations or background tasks.
    """

    async def _noop(*_args, **_kwargs):  # noqa: D401 – intentional stub
        return None

    mp = monkeypatch
    mp.setattr(
        "app.services.email_service.EmailService.send_email_verification",
        _noop,
        raising=False,
    )
    mp.setattr(
        "app.services.email_service.EmailService.send_password_reset",
        _noop,
        raising=False,
    )
    yield
