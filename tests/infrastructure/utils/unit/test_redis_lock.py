from unittest.mock import AsyncMock

import pytest

from app.utils.redis_lock import acquire_lock


@pytest.mark.asyncio
@pytest.mark.unit
async def test_acquire_lock_successfully():
    """
    Tests that the lock can be acquired successfully when it's not already held.
    """
    mock_redis = AsyncMock()
    mock_redis.set.return_value = True

    async with acquire_lock(mock_redis, "test-lock", timeout=10) as lock_acquired:
        assert lock_acquired is True
        mock_redis.set.assert_called_once_with(
            "lock:test-lock", "locked", nx=True, ex=10
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_acquire_lock_fails_when_already_held():
    """
    Tests that acquiring a lock fails if it is already held by another process.
    """
    mock_redis = AsyncMock()
    mock_redis.set.return_value = False

    async with acquire_lock(mock_redis, "test-lock", timeout=10) as lock_acquired:
        assert lock_acquired is False
        mock_redis.set.assert_called_once_with(
            "lock:test-lock", "locked", nx=True, ex=10
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_acquire_lock_cleanup_on_success():
    """Lock deletion is attempted when acquired."""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1

    async with acquire_lock(mock_redis, "cleanup", timeout=5) as acquired:
        assert acquired is True

    mock_redis.delete.assert_called_once_with("lock:cleanup")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_acquire_lock_no_cleanup_when_not_acquired():
    """No delete call when the lock was not obtained."""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = False

    async with acquire_lock(mock_redis, "nocleanup", timeout=5) as acquired:
        assert acquired is False

    mock_redis.delete.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_acquire_lock_delete_error_propagates():
    """Exceptions during cleanup bubble up."""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = True
    mock_redis.delete.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        async with acquire_lock(mock_redis, "err", timeout=1):
            pass


@pytest.mark.asyncio
@pytest.mark.unit
async def test_acquire_lock_set_error_propagates():
    """Errors acquiring the lock abort the context manager."""
    mock_redis = AsyncMock()
    mock_redis.set.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError, match="fail"):
        async with acquire_lock(mock_redis, "err", timeout=1):
            pass
