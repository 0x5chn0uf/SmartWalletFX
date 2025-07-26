from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.schemas.auth_token import TokenResponse
from app.models.user import User


class OAuthServiceInterface(ABC):
    """Interface for OAuth-based authentication helpers."""

    @abstractmethod
    async def authenticate_or_create(
        self, provider: str, account_id: str, email: Optional[str]
    ) -> User:
        """Authenticate a user via OAuth or create an account if needed."""

    @abstractmethod
    async def issue_tokens(self, user: User) -> TokenResponse:
        """Issue access and refresh tokens for *user*."""
