# flake8: noqa: E501

from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base
from app.services.snapshot_aggregation import SnapshotAggregationService

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _in_memory_session() -> Session:
    """Create an in-memory SQLite sync Session for testing."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return Session(bind=engine)


def _fake_metrics(user_address: str):  # noqa: D401
    """Return a dummy PortfolioMetrics-like object with required attrs."""
    now_ts = 1_700_000_000
    Dummy = SimpleNamespace  # Lightweight dynamic object
    metrics = Dummy(
        user_address=user_address,
        timestamp=Dummy(timestamp=lambda: None),
    )
    # Inject missing attributes
    metrics.timestamp = Dummy(timestamp=lambda: None)
    metrics.timestamp.timestamp = lambda: now_ts
    metrics.total_collateral = 100.0
    metrics.total_borrowings = 50.0
    metrics.total_collateral_usd = 120.0
    metrics.total_borrowings_usd = 60.0
    metrics.aggregate_health_score = 1.5
    metrics.aggregate_apy = 0.1
    metrics.collaterals = []
    metrics.borrowings = []
    metrics.staked_positions = []
    metrics.health_scores = []
    metrics.protocol_breakdown = {}
    return metrics


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_save_snapshot_sync_persists_row():
    session = _in_memory_session()

    service = SnapshotAggregationService(session, aggregator=_fake_metrics)

    snapshot = service.save_snapshot_sync("0xTEST")

    assert snapshot.id is not None
    assert snapshot.user_address == "0xTEST"

    # Verify record exists in DB
    fetched = session.get(type(snapshot), snapshot.id)
    assert fetched is not None
    assert fetched.user_address == "0xTEST"
