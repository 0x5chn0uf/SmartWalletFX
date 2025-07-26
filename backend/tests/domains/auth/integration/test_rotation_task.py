from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from app.tasks.jwt_rotation import _config, promote_and_retire_keys_task
from app.utils import jwt as jwt_utils

# ---------------------------------------------------------------------------
# Shared fixtures & helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch):
    """Snapshot & restore mutable settings between tests."""

    orig_keys = _config.JWT_KEYS.copy()
    orig_active = _config.ACTIVE_JWT_KID
    yield
    _config.JWT_KEYS = orig_keys
    _config.ACTIVE_JWT_KID = orig_active
    jwt_utils._RETIRED_KEYS.clear()  # pylint: disable=protected-access


@pytest.fixture(autouse=True)
def _patch_redis_and_lock(monkeypatch):
    """Patch Redis client builder and *acquire_lock* helper for isolation."""

    # Dummy async Redis client stub (close() must be await-able)
    class _DummyRedis:  # noqa: D401 – minimal stub
        async def close(self):  # noqa: D401 – async stub method
            return

    monkeypatch.setattr(
        "app.tasks.jwt_rotation._build_redis_client", lambda: _DummyRedis()
    )

    # Default: lock acquisition *succeeds* (individual tests may override)
    @asynccontextmanager
    async def _fake_lock(*_a, **_kw):  # noqa: D401 – test helper
        yield True

    monkeypatch.setattr("app.tasks.jwt_rotation.acquire_lock", _fake_lock)

    # Ensure JWKS cache invalidation does not spawn real async coroutines during tests.
    # This prevents "coroutine was never awaited" runtime warnings.
    monkeypatch.setattr(
        "app.utils.jwks_cache.invalidate_jwks_cache_sync",
        lambda: True,
    )


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


@freeze_time("2025-06-22 12:00:00")
def test_noop_run():
    """Task should exit early when no keys require action."""

    # Arrange – single active key, no retirements
    _config.JWT_KEYS = {"A": "secret-a"}
    _config.ACTIVE_JWT_KID = "A"

    # Act – run task synchronously (eager mode)
    promote_and_retire_keys_task()

    # Assert – state unchanged, no retired keys
    assert _config.ACTIVE_JWT_KID == "A"
    assert jwt_utils._RETIRED_KEYS == {}


@freeze_time("2025-06-22 12:00:00")
def test_retirement_only(monkeypatch):
    """If the active key's *retired_at* has passed, it is retired (no promotion when no *next* key)."""

    now = datetime.now(timezone.utc)

    # Arrange – single active key already expired
    _config.JWT_KEYS = {"A": "secret-a"}
    _config.ACTIVE_JWT_KID = "A"
    # Simulate that grace-period for A expired 1 second ago
    jwt_utils._RETIRED_KEYS["A"] = now - timedelta(
        seconds=1
    )  # pylint: disable=protected-access

    # Act
    promote_and_retire_keys_task()

    # Assert – key remains in retired map but timestamp updated to *now* (the task call)
    retired_at = jwt_utils._RETIRED_KEYS.get("A")  # pylint: disable=protected-access
    assert retired_at is not None and abs((retired_at - now).total_seconds()) < 1.0


@freeze_time("2025-06-22 12:00:00")
def test_promotion_and_retirement(monkeypatch):
    """When active key is retired and *next_kid* exists, promotion occurs and old key is retired."""

    now = datetime.now(timezone.utc)

    # Arrange – active key A expired, next key B is valid
    _config.JWT_KEYS = {"A": "secret-a", "B": "secret-b"}
    _config.ACTIVE_JWT_KID = "A"
    jwt_utils._RETIRED_KEYS["A"] = now - timedelta(
        seconds=1
    )  # pylint: disable=protected-access

    # Act
    promote_and_retire_keys_task()

    # Assert – B promoted, A retired (timestamp ~ now)
    assert _config.ACTIVE_JWT_KID == "B"
    retired_at = jwt_utils._RETIRED_KEYS.get("A")  # pylint: disable=protected-access
    assert retired_at is not None and abs((retired_at - now).total_seconds()) < 1.0


@freeze_time("2025-06-22 12:00:00")
def test_lock_contention(monkeypatch):
    """Task should exit quickly when distributed lock is not acquired."""

    # Arrange – active key A, next key B
    _config.JWT_KEYS = {"A": "secret-a", "B": "secret-b"}
    _config.ACTIVE_JWT_KID = "A"

    # Override *acquire_lock* to simulate contention (returns False)
    @asynccontextmanager
    async def _lock_contended(*_a, **_kw):  # noqa: D401 – test helper
        yield False

    monkeypatch.setattr("app.tasks.jwt_rotation.acquire_lock", _lock_contended)

    # Spy on helper to assert it is NOT called when lock missing
    helper_spy = MagicMock()
    monkeypatch.setattr("app.tasks.jwt_rotation.promote_and_retire_keys", helper_spy)

    # Act
    promote_and_retire_keys_task()

    # Assert – helper never executed, active kid unchanged
    helper_spy.assert_not_called()
    assert _config.ACTIVE_JWT_KID == "A"
