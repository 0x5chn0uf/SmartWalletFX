from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models.password_reset import PasswordReset


class PasswordResetRepositoryInterface(ABC):
    """Interface for password reset token persistence."""

    @abstractmethod
    async def create(
        self, token: str, user_id: UUID, expires_at: datetime
    ) -> PasswordReset:  # pragma: no cover
        """Create a new password reset token."""

    @abstractmethod
    async def get_valid(
        self, token: str
    ) -> Optional[PasswordReset]:  # pragma: no cover
        """Retrieve a valid (unexpired and unused) password reset token."""

    @abstractmethod
    async def mark_used(self, pr: PasswordReset) -> None:  # pragma: no cover
        """Mark the provided password reset token as used."""

    @abstractmethod
    async def delete_expired(self) -> int:  # pragma: no cover
        """Delete expired tokens and return the number removed."""
