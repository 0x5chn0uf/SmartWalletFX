"""Tests for the pure JWT rotation state-machine helper.

These tests intentionally begin with *failing* assertions to drive the TDD
cycle.  The very first test checks the *no-op* scenario: when
no keys are scheduled for retirement and the active key remains valid, the
helper should report that there is nothing to change.
"""

from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

from app.utils.jwt_rotation import Key, KeySet, promote_and_retire_keys


@freeze_time("2025-06-21 10:00:00")
@pytest.mark.unit
def test_no_keys_to_retire_or_promote():
    """A fresh key-set should result in a *no-op* update."""

    now = datetime.now(timezone.utc)
    kid = "keyA"
    key = Key(kid=kid, value="dummy")
    key_set = KeySet(keys={kid: key}, active_kid=kid, next_kid=None)

    update = promote_and_retire_keys(key_set, now)

    # Expect no changes (this will pass once logic is correct)
    assert update.is_noop()


@freeze_time("2025-06-21 10:00:00")
@pytest.mark.unit
def test_retire_key_and_promote_new_one():
    """When the active key has passed its *retired_at*, promote next_kid."""

    now = datetime.now(timezone.utc)
    old_kid = "keyA"
    new_kid = "keyB"

    # Old key expired 1 second ago
    old_key = Key(kid=old_kid, value="old", retired_at=now - timedelta(seconds=1))
    new_key = Key(kid=new_kid, value="new")

    key_set = KeySet(
        keys={old_kid: old_key, new_kid: new_key},
        active_kid=old_kid,
        next_kid=new_kid,
    )

    update = promote_and_retire_keys(key_set, now)

    assert update.new_active_kid == new_kid
    assert old_kid in update.keys_to_retire
