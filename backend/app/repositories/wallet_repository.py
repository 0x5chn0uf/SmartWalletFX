import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet


class WalletRepository:
    """Repository layer for wallet persistence operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    async def get_by_address(self, address: str) -> Optional[Wallet]:
        result = await self.db.execute(select(Wallet).where(Wallet.address == address))
        return result.scalars().first()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    async def create(
        self,
        address: str,
        user_id: uuid.UUID,
        name: Optional[str] = None,
    ) -> Wallet:
        """Create a wallet.

        Args:
            address: Wallet address.
            name: Optional display name.
            user_id: Owner user ID (required).
        """

        db_wallet = Wallet(
            user_id=user_id,
            address=address,
            name=name or "Unnamed Wallet",
            balance_usd=0.0,
        )
        self.db.add(db_wallet)
        try:
            await self.db.commit()
            await self.db.refresh(db_wallet)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail="Wallet address already exists")
        return db_wallet

    async def list_by_user(self, user_id: uuid.UUID) -> List[Wallet]:
        """Return wallets owned by *user_id*."""

        result = await self.db.execute(select(Wallet).where(Wallet.user_id == user_id))
        return result.scalars().all()

    async def delete(self, address: str, user_id: uuid.UUID) -> bool:
        """Delete wallet.

        Args:
            address: Wallet address to delete.
            user_id: Owner user ID (required for authorization).
        """

        wallet = await self.get_by_address(address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")

        if wallet.user_id != user_id:
            raise HTTPException(status_code=404, detail="Wallet not found")

        await self.db.delete(wallet)
        await self.db.commit()
        return True
