from contextlib import asynccontextmanager
from unittest.mock import MagicMock

from app.tasks.jwt_rotation import promote_and_retire_keys_task
from app.utils.jwt_rotation import KeySetUpdate  # local import


def test_promote_and_retire_keys_task_runs(monkeypatch):
    """Ensure the Celery task orchestrates helper invocation when lock is acquired."""

    # ------------------------------------------------------------------
    # Patch Redis lock to *always* acquire the lock.
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def _fake_lock(*_a, **_kw):  # noqa: D401 – test helper
        yield True

    monkeypatch.setattr("app.tasks.jwt_rotation.acquire_lock", _fake_lock, raising=True)

    # ------------------------------------------------------------------
    # Patch helper & apply function so we can assert they're called.
    # ------------------------------------------------------------------

    fake_update = KeySetUpdate(new_active_kid="newkey", keys_to_retire=set())

    monkeypatch.setattr(
        "app.tasks.jwt_rotation.promote_and_retire_keys",
        MagicMock(return_value=fake_update),
        raising=True,
    )
    apply_spy = MagicMock()
    monkeypatch.setattr("app.tasks.jwt_rotation._apply_key_set_update", apply_spy)

    # ------------------------------------------------------------------
    # Patch Redis client builder to avoid external dependency.
    # ------------------------------------------------------------------

    class _DummyRedis:
        async def close(self):  # noqa: D401 – async stub
            pass

    monkeypatch.setattr(
        "app.tasks.jwt_rotation._build_redis_client",
        lambda: _DummyRedis(),
    )

    # ------------------------------------------------------------------
    # Run task in *eager* mode (synchronous) – call the underlying function
    # directly for simplicity.
    # ------------------------------------------------------------------
    promote_and_retire_keys_task()

    # Assert helper and apply were invoked
    assert (
        apply_spy.called
    ), "_apply_key_set_update should be called when update != noop"
