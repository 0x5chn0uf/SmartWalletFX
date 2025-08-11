from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.models.oauth_account import OAuthAccount


class OAuthAccountRepositoryInterface(ABC):
    """Interface for OAuth account persistence."""

    @abstractmethod
    async def get_by_provider_account(
        self, provider: str, account_id: str
    ) -> Optional[OAuthAccount]:  # pragma: no cover
        """Return account by provider and account id."""

    @abstractmethod
    async def get_by_user_provider(
        self, user_id: UUID, provider: str
    ) -> Optional[OAuthAccount]:  # pragma: no cover
        """Return account by user id and provider."""

    @abstractmethod
    async def link_account(
        self, user_id: UUID, provider: str, account_id: str, email: str | None = None
    ) -> OAuthAccount:  # pragma: no cover
        """Link an OAuth account to a user."""
