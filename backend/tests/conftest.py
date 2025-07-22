# flake8: noqa

import pathlib
from datetime import timedelta

import pytest
from alembic import command
from alembic.config import Config
from hypothesis import settings

from .shared.fixtures.auth import *
from .shared.fixtures.base import *
from .shared.fixtures.client import *
from .shared.fixtures.core import *
from .shared.fixtures.database import *
from .shared.fixtures.di_container import *
from .shared.fixtures.endpoints import *
from .shared.fixtures.jwks import *
from .shared.fixtures.mocks import *
from .shared.fixtures.repositories import *
from .shared.fixtures.services import *
from .shared.fixtures.usecases import *

ALEMBIC_CONFIG_PATH = str(pathlib.Path(__file__).parent.parent / "alembic.ini")

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


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    """Ensure the database schema is up-to-date for the test session.

    Runs ``alembic upgrade head`` against the *configured* database before the
    first test executes.  This avoids "relation ... does not exist" errors when
    the CI database is freshly created.
    """

    cfg = Config(ALEMBIC_CONFIG_PATH)
    command.upgrade(cfg, "head")
