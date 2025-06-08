from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models import Wallet


class WalletStore:
    @staticmethod
    async def get_by_address(db: AsyncSession, address: str) -> Optional[Wallet]:
        result = await db.execute(select(Wallet).where(Wallet.address == address))
        return result.scalars().first()

    @staticmethod
    async def create(
        db: AsyncSession, address: str, name: Optional[str] = None
    ) -> Wallet:
        db_wallet = Wallet(address=address, name=name)
        db.add(db_wallet)
        try:
            await db.commit()
            await db.refresh(db_wallet)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=400, detail="Wallet address already exists")
        return db_wallet

    @staticmethod
    async def list_all(db: AsyncSession) -> List[Wallet]:
        result = await db.execute(select(Wallet))
        return result.scalars().all()

    @staticmethod
    async def delete(db: AsyncSession, address: str) -> bool:
        wallet = await WalletStore.get_by_address(db, address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        await db.delete(wallet)
        await db.commit()
        return True
