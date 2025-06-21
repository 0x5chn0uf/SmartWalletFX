from unittest.mock import AsyncMock

import pytest

from app.utils.redis_lock import acquire_lock


@pytest.mark.asyncio
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
