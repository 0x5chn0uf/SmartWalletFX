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

    async def create(self, address: str, name: Optional[str] = None) -> Wallet:
        db_wallet = Wallet(address=address, name=name, balance=0.0)
        self.db.add(db_wallet)
        try:
            await self.db.commit()
            await self.db.refresh(db_wallet)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail="Wallet address already exists")
        return db_wallet

    async def list_all(self) -> List[Wallet]:
        result = await self.db.execute(select(Wallet))
        return result.scalars().all()

    async def delete(self, address: str) -> bool:
        wallet = await self.get_by_address(address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        await self.db.delete(wallet)
        await self.db.commit()
        return True
