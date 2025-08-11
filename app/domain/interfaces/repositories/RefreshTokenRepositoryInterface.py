from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.models.refresh_token import RefreshToken


class RefreshTokenRepositoryInterface(ABC):
    """Interface for refresh token persistence."""

    @abstractmethod
    async def save(self, token: RefreshToken) -> RefreshToken:  # pragma: no cover
        """Persist a refresh token."""

    @abstractmethod
    async def get_by_jti_hash(
        self, jti_hash: str
    ) -> Optional[RefreshToken]:  # pragma: no cover
        """Return a refresh token by its hashed JTI."""

    @abstractmethod
    async def revoke(self, token: RefreshToken) -> None:  # pragma: no cover
        """Mark the provided refresh token as revoked."""

    @abstractmethod
    async def delete_expired(
        self, *, before: datetime | None = None
    ) -> int:  # pragma: no cover
        """Delete tokens expired before *before* and return the number removed."""

    @abstractmethod
    async def create_from_jti(
        self, jti: str, user_id: UUID, ttl: timedelta
    ) -> RefreshToken:  # pragma: no cover
        """Create and persist a token from a raw JTI."""
