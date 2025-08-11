from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Dict


class JWTUtilsInterface(ABC):
    """Interface for JWT helper methods."""

    @abstractmethod
    def create_access_token(
        self,
        subject: str | int,
        *,
        expires_delta: timedelta | None = None,
        additional_claims: Dict[str, Any] | None = None,
    ) -> str:
        """Create an access token."""

    @abstractmethod
    def create_refresh_token(self, subject: str | int) -> str:
        """Create a refresh token."""
