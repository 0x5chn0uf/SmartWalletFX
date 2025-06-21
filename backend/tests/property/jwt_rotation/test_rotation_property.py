"""Property-based tests for the JWT rotation state-machine.

These tests generate random key-sets and timestamps to validate that
`promote_and_retire_keys` never violates fundamental invariants:

1. `keys_to_retire` ⊆ existing keys.
2. `new_active_kid`, if set, equals the provided `next_kid` and is **not**
   included in `keys_to_retire`.
3. All keys scheduled for retirement have `retired_at` ≤ *now*.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from hypothesis import given, settings
from hypothesis import strategies as st

from app.utils.jwt_rotation import Key, KeySet, promote_and_retire_keys


@st.composite
def key_strategy(draw) -> Key:  # type: ignore[valid-type]
    kid = draw(
        st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(blacklist_categories=["Cs", "Cc"]),
        )
    )
    value = draw(st.text(min_size=1, max_size=20))
    # 30% chance of having a retired_at timestamp in the past, 10% in future
    retired_opt = draw(st.floats(min_value=0, max_value=1))
    retired_at: Optional[datetime] = None
    if retired_opt < 0.3:
        retired_at = datetime.now(timezone.utc) - timedelta(
            seconds=draw(st.integers(min_value=1, max_value=3600))
        )
    elif retired_opt < 0.4:
        retired_at = datetime.now(timezone.utc) + timedelta(
            seconds=draw(st.integers(min_value=1, max_value=3600))
        )
    return Key(kid=kid, value=value, retired_at=retired_at)


@st.composite
def keyset_strategy(draw) -> KeySet:  # type: ignore[valid-type]
    # Generate between 1 and 5 distinct keys
    keys = draw(
        st.lists(key_strategy(), min_size=1, max_size=5, unique_by=lambda k: k.kid)
    )
    key_map: Dict[str, Key] = {k.kid: k for k in keys}
    active_kid = draw(st.sampled_from(list(key_map.keys())))

    # 50% chance of having a *next_kid*
    next_kid: Optional[str] = None
    if draw(st.booleans()):
        # pick a different key if possible else None
        choices = [kid for kid in key_map.keys() if kid != active_kid]
        if choices:
            next_kid = draw(st.sampled_from(choices))
    grace_seconds = draw(st.integers(min_value=60, max_value=7200))
    return KeySet(
        keys=key_map,
        active_kid=active_kid,
        next_kid=next_kid,
        grace_period_seconds=grace_seconds,
    )


@given(keyset=keyset_strategy())
@settings(max_examples=100)
def test_rotation_invariants(keyset: KeySet):
    now = datetime.now(timezone.utc)
    update = promote_and_retire_keys(keyset, now)

    # 1. keys_to_retire subset of existing kids
    assert update.keys_to_retire.issubset(set(keyset.keys.keys()))

    # 2. new_active_kid invariants
    if update.new_active_kid is not None:
        assert update.new_active_kid == keyset.next_kid
        assert update.new_active_kid not in update.keys_to_retire

    # 3. every kid slated for retirement must have retired_at <= now
    for kid in update.keys_to_retire:
        assert kid in keyset.keys
        retired_at = keyset.keys[kid].retired_at
        assert retired_at is not None and retired_at <= now
