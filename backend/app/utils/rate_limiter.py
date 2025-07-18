"""Simple in-memory rate-limiter used for login brute-force protection.

For production deployments a shared cache such as Redis **must** replace
this implementation.  The current design is intentionally minimal to
support CI tests and local development without external dependencies.
"""
from __future__ import annotations

from collections import defaultdict
from time import time
from typing import DefaultDict, List

from app.core.config import Configuration


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


class RateLimiterUtils:
    """Utility class for rate limiting operations."""

    def __init__(self, config: Configuration):
        """Initialize RateLimiterUtils with dependencies."""
        self.__config = config
        self.__login_rate_limiter = InMemoryRateLimiter(
            max_attempts=config.AUTH_RATE_LIMIT_ATTEMPTS,
            window_seconds=config.AUTH_RATE_LIMIT_WINDOW_SECONDS,
        )

    @property
    def login_rate_limiter(self) -> InMemoryRateLimiter:
        """Get the login rate limiter instance."""
        return self.__login_rate_limiter


# ----------------------------------------------------------------------
# Default instance for backward compatibility
# ----------------------------------------------------------------------
_default_rate_limiter_utils = RateLimiterUtils(Configuration())
login_rate_limiter = _default_rate_limiter_utils.login_rate_limiter

__all__ = [
    "InMemoryRateLimiter",
    "RateLimiterUtils",
    "login_rate_limiter",
]
