from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models.email_verification import EmailVerification


class EmailVerificationRepositoryInterface(ABC):
    """Interface for email verification token persistence."""

    @abstractmethod
    async def create(
        self, token: str, user_id: UUID, expires_at: datetime
    ) -> EmailVerification:  # pragma: no cover
        """Create a new email verification token."""

    @abstractmethod
    async def get_valid(
        self, token: str
    ) -> Optional[EmailVerification]:  # pragma: no cover
        """Retrieve a valid (unexpired and unused) verification token."""

    @abstractmethod
    async def mark_used(self, ev: EmailVerification) -> None:  # pragma: no cover
        """Mark the provided token as used."""

    @abstractmethod
    async def delete_expired(self) -> int:  # pragma: no cover
        """Delete expired tokens and return the number removed."""
