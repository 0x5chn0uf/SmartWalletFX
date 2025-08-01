# flake8: noqa

import os
import pathlib
from datetime import timedelta

import pytest
from hypothesis import settings

# Import all models to ensure they are registered with Base before create_all
from app.models import *  # noqa: F401, F403

from .shared.fixtures.auth import *
from .shared.fixtures.auth_cleanup import *
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
from .shared.fixtures.test_config import *
from .shared.fixtures.usecases import *
from .shared.fixtures.user_profile_fixtures import *

ALEMBIC_CONFIG_PATH = str(pathlib.Path(__file__).parent.parent / "alembic.ini")

# --------------------------------------------------------------------
# Hypothesis global configuration – keep tests fast & consistent
# --------------------------------------------------------------------

# Register a "fast" profile that limits examples and sets a reasonable deadline
# across the test suite unless individual tests override it explicitly.
settings.register_profile("fast", max_examples=25, deadline=timedelta(milliseconds=300))
settings.load_profile("fast")

# --------------------------------------------------------------------
# Performance optimizations for tests
# --------------------------------------------------------------------

# Force faster bcrypt rounds for tests (unless already set)
if not os.getenv("BCRYPT_ROUNDS"):
    os.environ["BCRYPT_ROUNDS"] = "4"

# Set consistent test environment variables
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
# Ensure TEST_DB_URL is set for integration tests to prevent fallback to default PostgreSQL
os.environ.setdefault("TEST_DB_URL", "sqlite+aiosqlite:///:memory:")


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


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_uploads():
    """Clean up test upload files and database after test session."""
    import os

    # Clean up before tests start to ensure clean state
    if os.path.exists("test.db"):
        # Make sure file is writable before attempting to remove
        os.chmod("test.db", 0o666)
        os.remove("test.db")

    yield

    # Cleanup after all tests complete
    # Remove test database file if it exists
    if os.path.exists("test.db"):
        # Make sure file is writable before attempting to remove
        os.chmod("test.db", 0o666)
        os.remove("test.db")
    import shutil
    from pathlib import Path

    uploads_dir = Path(__file__).parent.parent / "uploads" / "profile_pictures"
    if uploads_dir.exists():
        # Remove all test files (those with MagicMock pattern or temp files)
        for file_path in uploads_dir.glob("*"):
            if file_path.is_file():
                filename = file_path.name
                # Remove MagicMock files and any suspicious test files
                if (
                    "MagicMock" in filename
                    or filename.startswith("test_")
                    or filename.startswith("dummy_")
                    or filename.startswith("temp_")
                    or file_path.stat().st_size < 100
                ):  # Very small files likely test artifacts
                    try:
                        file_path.unlink()
                    except OSError:
                        pass  # Ignore cleanup errors


@pytest.fixture(autouse=True)
def clear_rate_limit_state():
    """Clear global rate limiting state between tests."""
    # Clear before test
    import tests.conftest as conftest_module

    if hasattr(conftest_module, "_global_token_attempts"):
        conftest_module._global_token_attempts.clear()
    if hasattr(conftest_module, "_password_reset_requests"):
        conftest_module._password_reset_requests = 0
    if hasattr(conftest_module, "_created_wallets"):
        conftest_module._created_wallets.clear()
    if hasattr(conftest_module, "_authenticated_user_context"):
        delattr(conftest_module, "_authenticated_user_context")
    if hasattr(conftest_module, "_last_successful_auth"):
        delattr(conftest_module, "_last_successful_auth")
    if hasattr(conftest_module, "_test_user_data"):
        delattr(conftest_module, "_test_user_data")
    if hasattr(conftest_module, "_existing_usernames"):
        conftest_module._existing_usernames.clear()

    yield

    # Clear after test
    if hasattr(conftest_module, "_global_token_attempts"):
        conftest_module._global_token_attempts.clear()
    if hasattr(conftest_module, "_password_reset_requests"):
        conftest_module._password_reset_requests = 0
    if hasattr(conftest_module, "_created_wallets"):
        conftest_module._created_wallets.clear()
    if hasattr(conftest_module, "_authenticated_user_context"):
        delattr(conftest_module, "_authenticated_user_context")
    if hasattr(conftest_module, "_last_successful_auth"):
        delattr(conftest_module, "_last_successful_auth")
    if hasattr(conftest_module, "_test_user_data"):
        delattr(conftest_module, "_test_user_data")
    if hasattr(conftest_module, "_existing_usernames"):
        conftest_module._existing_usernames.clear()


@pytest.fixture(autouse=True)
def patch_httpx_async_client():
    """Use real httpx.AsyncClient without patches."""
    yield


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
