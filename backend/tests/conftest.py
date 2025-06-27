# flake8: noqa

import asyncio
import datetime
import pathlib
import uuid

import pytest
from fastapi.testclient import TestClient
from hypothesis import settings

from app.core.database import get_db
from app.usecase.portfolio_aggregation_usecase import PortfolioMetrics
from app.utils import security

from .fixtures.auth import *
from .fixtures.base import *
from .fixtures.database import *
from .fixtures.mocks import *
from .fixtures.portfolio import *

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


@pytest.fixture(scope="session")
def anyio_backend():
    """Force AnyIO to use only the asyncio backend during tests."""
    return "asyncio"


# --------------------------------------------------------------------
# Hypothesis global configuration – keep tests fast & consistent
# --------------------------------------------------------------------

# Register a "fast" profile that limits examples and sets a reasonable deadline
# across the test suite unless individual tests override it explicitly.
settings.register_profile(
    "fast", max_examples=25, deadline=datetime.timedelta(milliseconds=300)
)
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
