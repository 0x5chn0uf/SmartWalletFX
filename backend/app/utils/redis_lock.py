from contextlib import asynccontextmanager
from typing import AsyncGenerator

from redis.asyncio import Redis


@asynccontextmanager
async def acquire_lock(
    redis: Redis, lock_name: str, timeout: int
) -> AsyncGenerator[bool, None]:
    """
    An async context manager to acquire a distributed lock in Redis.

    Args:
        redis: An asynchronous Redis client instance.
        lock_name: A unique name for the lock.
        timeout: The lock's time-to-live in seconds.

    Yields:
        A boolean indicating if the lock was successfully acquired.
    """
    lock_key = f"lock:{lock_name}"
    lock_acquired = await redis.set(lock_key, "locked", nx=True, ex=timeout)
    try:
        yield lock_acquired
    finally:
        if lock_acquired:
            # Clean up the lock if we acquired it.
            # This is not strictly necessary due to the TTL, but it's good practice.
            await redis.delete(lock_key)
