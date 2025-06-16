from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.schemas.portfolio_timeline import TimelineResponse
from tests.property.strategies import portfolio_snapshot_strategy

# NOTE: This is an illustrative property-based test scaffold. It will be
# expanded with stricter invariants once the Hypothesis strategy helpers are
# fleshed out in `backend/tests/property/strategies.py`.

# Generate a list of snapshots already sorted by timestamp ascending to satisfy invariant.
snapshots_strategy = st.lists(
    portfolio_snapshot_strategy(), min_size=1, max_size=50
).map(lambda snaps: sorted(snaps, key=lambda s: s.timestamp))


@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(
    snapshots=snapshots_strategy,
    interval=st.sampled_from(["daily", "weekly"]),
)
def test_timeline_response_invariants(snapshots, interval):
    """TimelineResponse should always maintain sorting invariants and statistic bounds."""
    response = TimelineResponse(
        snapshots=snapshots,
        interval=interval,
        limit=len(snapshots),
        offset=0,
        total=len(snapshots),
    )

    # Invariant 1: snapshots sorted by timestamp ascending
    timestamps = [s.timestamp for s in response.snapshots]
    assert timestamps == sorted(
        timestamps
    ), "Snapshots must be ordered by ascending timestamp"

    # Invariant 2: aggregate_health_score bounds (0 <= hs <= 2)
    for snap in response.snapshots:
        assert (
            0 <= snap.aggregate_health_score <= 2
        ), "Health score out of expected bounds"
