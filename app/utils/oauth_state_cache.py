from __future__ import annotations

import time
import uuid
from typing import Dict

from redis.asyncio import Redis

# ---------------------------------------------------------------------------
# OAuth "state" caching helpers
# ---------------------------------------------------------------------------

# Key prefix in Redis where we store a temporary value signalling that a state
# parameter is valid for the current OAuth login flow.
STATE_PREFIX = "oauth:state:"

# Default Time-To-Live for a state entry – 5 minutes per OAuth best practices.
DEFAULT_TTL_SEC = 300

# --- In-memory fallback -----------------------------------------------------
# In local development environments Redis might be unavailable or misconfigured.
# Instead of failing the entire OAuth flow we fall back to an in-memory cache.
# This is **NOT** suitable for production because it is process-local and will
# not work across multiple worker processes or instances.

_memory_state_cache: Dict[str, float] = {}


def generate_state() -> str:
    return uuid.uuid4().hex


async def store_state(redis: Redis, state: str, ttl: int = DEFAULT_TTL_SEC) -> bool:
    """Store *state* in Redis, falling back to in-memory cache on error.

    Returns True on success, False otherwise.
    """

    try:
        await redis.setex(f"{STATE_PREFIX}{state}", ttl, "1")
        return True
    except Exception as exc:  # pragma: no cover – log-only
        # Redis unavailable – degrade gracefully for local dev
        import logging

        logging.warning(
            "Redis unavailable – falling back to in-memory state cache: %s", exc
        )
        _memory_state_cache[state] = time.monotonic() + ttl
        return True


async def verify_state(redis: Redis, state: str) -> bool:
    """Verify and delete *state* token. Falls back to in-memory cache."""

    try:
        key = f"{STATE_PREFIX}{state}"
        exists = await redis.exists(key)
        if exists:
            await redis.delete(key)
            return True
    except Exception as exc:  # pragma: no cover – log-only
        # Redis unavailable, fall back to in-memory cache
        import logging

        logging.warning("Redis unavailable during state verify – falling back: %s", exc)

    # Fallback check
    expiry = _memory_state_cache.pop(state, None)
    if expiry is not None and expiry > time.monotonic():
        return True

    return False
