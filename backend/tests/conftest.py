# flake8: noqa

import contextlib
import datetime
import os
import pathlib
import subprocess
import sys
import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from freezegun import freeze_time
from hypothesis import settings
from sqlalchemy import create_engine  # sync version
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
from app.models import Base
from app.usecase.portfolio_aggregation_usecase import PortfolioMetrics

# ----------------------------------------------------------------------------
# Per-test database file helper
# ----------------------------------------------------------------------------

ALEMBIC_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../alembic.ini")
)


def _make_test_db(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
    """Return (async_url, sync_url) for a fresh SQLite file under tmp dir."""

    db_dir = tmp_path_factory.mktemp("db")
    db_file = db_dir / "test.sqlite"
    async_url = f"sqlite+aiosqlite:///{db_file}"
    sync_url = f"sqlite:///{db_file}"

    # Run Alembic migrations synchronously against *sync_url*
    env = os.environ.copy()
    env["TEST_DB_URL"] = sync_url
    subprocess.run(
        ["alembic", "-c", ALEMBIC_CONFIG_PATH, "upgrade", "head"], check=True, env=env
    )

    return async_url, sync_url


# ----------------------------------------------------------------------------
# Async engine & DB session fixtures (no SAVEPOINTs)
# ----------------------------------------------------------------------------


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


@pytest_asyncio.fixture
async def db_session(async_engine):
    """Plain AsyncSession bound to the per-test database file."""

    async_session = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


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

    # Reuse existing app instance instead of creating a new one each time
    from app.main import app as _app

    yield _app


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

    # Reuse the same temp DB file created by the *async_engine* fixture so
    # that Celery tasks / sync code share state with the async side.
    sync_url = os.environ.get("TEST_DB_URL", "sqlite:///./smartwallet_test.db")

    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False})

    SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    db_mod.sync_engine = sync_engine
    db_mod.SyncSessionLocal = SyncSessionLocal
    snapshots_mod.SyncSessionLocal = SyncSessionLocal

    # Ensure DI helpers use the same session factory
    import app.di as di_mod

    di_mod.SyncSessionLocal = SyncSessionLocal

    yield


@pytest.fixture(autouse=True)
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


@pytest.fixture
def freezer():  # noqa: D401
    """Fixture that provides a context manager for freezing time.

    Any calls to datetime.datetime.now() or utcnow() will return the same
    timestamp within the with block.

    Yields:
        A context manager for freezing time.
    """

    @contextlib.contextmanager
    def _freezer(timestamp: str | datetime.datetime):
        with freeze_time(timestamp):
            yield

    return _freezer


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear the in-memory rate limiter's storage between tests."""
    from app.utils.rate_limiter import login_rate_limiter

    login_rate_limiter.clear()
    yield
    login_rate_limiter.clear()


# --------------------------------------------------------------------
# Performance patch – cache RSA key generation to speed up Hypothesis
# --------------------------------------------------------------------

# Generating real 2048-bit RSA keys is computationally expensive and causes
# Hypothesis' *too_slow* health-check to fail when the strategy in
# *tests/property/jwks/test_jwks_property.py* requests many keys per test
# run.  We work around this by monkey-patching
# ``cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key`` with
# a lightweight stub that returns a **pre-generated** key, thereby reducing
# the per-example overhead from hundreds of milliseconds to microseconds.

from cryptography.hazmat.primitives.asymmetric import rsa as _rsa

_CACHED_TEST_PRIVATE_KEY = _rsa.generate_private_key(
    public_exponent=65537, key_size=1024
)


def _fast_generate_private_key(
    public_exponent: int, key_size: int, backend=None
):  # noqa: D401
    """Return a cached test key rather than generating a new one each call.

    The *public_exponent*, *key_size*, and *backend* parameters are accepted
    for signature-compatibility but ignored – tests do not depend on their
    exact values, only that a compatible key object is returned.
    """

    return _CACHED_TEST_PRIVATE_KEY


# Apply the monkey-patch **before** tests import the function.
_rsa.generate_private_key = _fast_generate_private_key


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Creates and returns a user for testing."""
    from app.schemas.user import UserCreate
    from app.services.auth_service import AuthService

    service = AuthService(db_session)
    user_in = UserCreate(
        username=f"user-{uuid.uuid4()}",
        email=f"{uuid.uuid4()}@test.com",
        password="S3cur3!pwd",
    )
    user = await service.register(user_in)
    return user


@pytest_asyncio.fixture
async def authenticated_client(db_session: AsyncSession, test_app, test_user):
    """
    Creates a user, logs them in, and yields an authenticated AsyncClient.
    """
    # Log in the user created by the test_user fixture
    from httpx import AsyncClient

    from app.services.auth_service import AuthService

    service = AuthService(db_session)
    token_data = await service.authenticate(test_user.username, "S3cur3!pwd")
    token = token_data.access_token
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(app=test_app, base_url="http://test", headers=headers) as ac:
        yield ac


# --------------------------------------------------------------------
# Per-test DB cleanup (isolation without expensive migrations per test)
# --------------------------------------------------------------------


from sqlalchemy import text  # placed after SQLAlchemy is available


@pytest_asyncio.fixture(autouse=True)
async def _clean_database(async_engine):
    """Delete all rows from every table after each test function.

    This provides strong isolation while keeping the schema intact so we
    avoid the cost of replaying Alembic migrations for every single test.
    """

    yield  # run the test

    async with async_engine.begin() as conn:
        # Temporarily disable FK constraints for SQLite to allow arbitrary
        # deletion order without worrying about relationships.
        await conn.execute(text("PRAGMA foreign_keys = OFF"))

        for tbl in Base.metadata.sorted_tables:
            try:
                await conn.execute(text(f'DELETE FROM "{tbl.name}"'))
            except (
                Exception
            ):  # noqa: BLE001 – ignore tables not present in SQLite test DB
                # Table may not exist if corresponding migration hasn't run yet.
                continue

        await conn.execute(text("PRAGMA foreign_keys = ON"))


# --------------------------------------------------------------------
# Session-scoped asyncio event-loop (required by session-scoped async fixtures)
# --------------------------------------------------------------------


import asyncio


@pytest.fixture(scope="session")
def event_loop():  # noqa: D401 – pytest asyncio helper
    """Create a dedicated asyncio loop for the entire test session."""

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def create_user_and_wallet(db_session: AsyncSession):
    """Factory fixture to create a user and a wallet for them."""

    async def _factory():
        from app.models.wallet import Wallet
        from app.repositories.wallet_repository import WalletRepository
        from app.schemas.user import UserCreate
        from app.services.auth_service import AuthService

        # Create user
        service = AuthService(db_session)
        user_in = UserCreate(
            username=f"user-{uuid.uuid4()}",
            email=f"{uuid.uuid4()}@test.com",
            password="S3cur3!pwd",
        )
        user = await service.register(user_in)

        # Create wallet
        repo = WalletRepository(db_session)
        wallet = await repo.create(
            user_id=user.id,
            address=f"0x{uuid.uuid4().hex[:40]}",
            name="Test Wallet",
        )
        return user, wallet

    return _factory
