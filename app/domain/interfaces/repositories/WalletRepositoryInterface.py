from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.models.wallet import Wallet


class WalletRepositoryInterface(ABC):
    """Interface for wallet persistence."""

    @abstractmethod
    async def get_by_address(
        self, address: str
    ) -> Optional[Wallet]:  # pragma: no cover
        """Retrieve a wallet by address."""

    @abstractmethod
    async def create(
        self, address: str, user_id: UUID, name: str | None = None
    ) -> Wallet:  # pragma: no cover
        """Create a new wallet."""

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[Wallet]:  # pragma: no cover
        """List wallets owned by a user."""

    @abstractmethod
    async def delete(self, address: str, user_id: UUID) -> bool:  # pragma: no cover
        """Delete a wallet owned by *user_id* by address."""
