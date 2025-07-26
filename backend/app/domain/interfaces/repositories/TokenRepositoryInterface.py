from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.schemas.token import TokenCreate
from app.models.token import Token


class TokenRepositoryInterface(ABC):
    """Interface for token persistence."""

    @abstractmethod
    async def create(self, data: TokenCreate) -> Token:  # pragma: no cover
        """Create a new token."""
