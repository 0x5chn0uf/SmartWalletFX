from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.schemas.token_balance import TokenBalanceCreate
from app.models.token_balance import TokenBalance


class TokenBalanceRepositoryInterface(ABC):
    """Interface for token balance persistence."""

    @abstractmethod
    async def create(
        self, data: TokenBalanceCreate
    ) -> TokenBalance:  # pragma: no cover
        """Create a new token balance record."""
