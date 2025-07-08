from unittest.mock import AsyncMock

import pytest

from app.utils.oauth_state_cache import (
    generate_state,
    store_state,
    verify_state,
)


@pytest.mark.asyncio
async def test_generate_state_unique():
    state1 = generate_state()
    state2 = generate_state()
    assert state1 != state2
    assert len(state1) == 32


@pytest.mark.asyncio
async def test_store_state_success():
    redis = AsyncMock()
    result = await store_state(redis, "abc", ttl=5)
    redis.setex.assert_awaited_with("oauth:state:abc", 5, "1")
    assert result is True


@pytest.mark.asyncio
async def test_store_state_failure():
    redis = AsyncMock()
    redis.setex.side_effect = Exception("boom")
    result = await store_state(redis, "abc")
    assert result is False


@pytest.mark.asyncio
async def test_verify_state_hit():
    redis = AsyncMock()
    redis.exists.return_value = 1
    result = await verify_state(redis, "abc")
    redis.delete.assert_awaited_with("oauth:state:abc")
    assert result is True


@pytest.mark.asyncio
async def test_verify_state_miss():
    redis = AsyncMock()
    redis.exists.return_value = 0
    result = await verify_state(redis, "abc")
    redis.delete.assert_not_called()
    assert result is False


@pytest.mark.asyncio
async def test_verify_state_exception():
    redis = AsyncMock()
    redis.exists.side_effect = Exception("boom")
    result = await verify_state(redis, "abc")
    assert result is False
