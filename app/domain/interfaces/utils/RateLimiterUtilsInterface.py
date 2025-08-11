from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from app.utils.rate_limiter import InMemoryRateLimiter


class RateLimiterUtilsInterface(ABC):
    """Interface for rate limiter utilities."""

    @property
    @abstractmethod
    def login_rate_limiter(self) -> InMemoryRateLimiter:
        """Return the login rate limiter instance."""
