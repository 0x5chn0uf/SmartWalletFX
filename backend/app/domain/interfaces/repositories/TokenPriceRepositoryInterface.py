from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.schemas.token_price import TokenPriceCreate
from app.models.token_price import TokenPrice


class TokenPriceRepositoryInterface(ABC):
    """Interface for token price persistence."""

    @abstractmethod
    async def create(self, data: TokenPriceCreate) -> TokenPrice:  # pragma: no cover
        """Create a new token price record."""
