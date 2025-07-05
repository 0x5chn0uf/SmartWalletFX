"""Simple in-memory rate-limiter used for login brute-force protection.

For production deployments a shared cache such as Redis **must** replace
this implementation.  The current design is intentionally minimal to
support CI tests and local development without external dependencies.
"""
from __future__ import annotations

from collections import defaultdict
from time import time
from typing import DefaultDict, List

from app.core.config import settings


class InMemoryRateLimiter:
    """Thread-unsafe naïve rate-limiter (per-process memory)."""

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: DefaultDict[str, List[float]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def allow(self, key: str) -> bool:
        """Return **True** if another attempt is allowed for *key*."""
        now = time()
        window_start = now - self.window_seconds
        hits = [ts for ts in self._hits[key] if ts >= window_start]
        self._hits[key] = hits  # prune old hits
        if len(hits) >= self.max_attempts:
            return False
        hits.append(now)
        return True

    def clear(self) -> None:  # pragma: no cover – test helper
        """Reset the internal hit-store (used in tests)."""

        self._hits.clear()

    def reset(self, key: str) -> None:  # pragma: no cover – helper
        """Clear stored hits for *key* without affecting others."""

        if key in self._hits:
            self._hits[key].clear()


# ----------------------------------------------------------------------
# Singleton instance configured from settings
# ----------------------------------------------------------------------

login_rate_limiter = InMemoryRateLimiter(
    max_attempts=settings.AUTH_RATE_LIMIT_ATTEMPTS,
    window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
)

__all__ = [
    "InMemoryRateLimiter",
    "login_rate_limiter",
]
