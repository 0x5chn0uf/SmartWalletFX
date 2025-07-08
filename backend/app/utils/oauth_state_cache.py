from __future__ import annotations

import uuid
from typing import Optional

from redis.asyncio import Redis

STATE_PREFIX = "oauth:state:"
DEFAULT_TTL_SEC = 300


def generate_state() -> str:
    return uuid.uuid4().hex


async def store_state(redis: Redis, state: str, ttl: int = DEFAULT_TTL_SEC) -> bool:
    try:
        await redis.setex(f"{STATE_PREFIX}{state}", ttl, "1")
        return True
    except Exception:  # pragma: no cover - log-only
        return False


async def verify_state(redis: Redis, state: str) -> bool:
    try:
        key = f"{STATE_PREFIX}{state}"
        exists = await redis.exists(key)
        if exists:
            await redis.delete(key)
        return bool(exists)
    except Exception:  # pragma: no cover - log-only
        return False
