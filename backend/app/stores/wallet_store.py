from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet


class WalletStore:
    """
    Store layer for wallet persistence operations.
    Handles database access for creating, retrieving, listing, and
    deleting wallets.
    """

    @staticmethod
    async def get_by_address(
        db: AsyncSession, address: str
    ) -> Optional[Wallet]:
        """
        Retrieve a wallet by its address.
        Args:
            db: Async database session.
            address: Wallet address to retrieve.
        Returns:
            Optional[Wallet]: The wallet instance if found, else None.
        """
        result = await db.execute(
            select(Wallet).where(Wallet.address == address)
        )
        return result.scalars().first()

    @staticmethod
    async def create(
        db: AsyncSession, address: str, name: Optional[str] = None
    ) -> Wallet:
        """
        Create a new wallet in the database.
        Args:
            db: Async database session.
            address: Wallet address.
            name: Wallet name.
        Returns:
            Wallet: The created wallet instance.
        """
        db_wallet = Wallet(address=address, name=name)
        db.add(db_wallet)
        try:
            await db.commit()
            await db.refresh(db_wallet)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=400, detail="Wallet address already exists"
            )
        return db_wallet

    @staticmethod
    async def list_all(db: AsyncSession) -> List[Wallet]:
        """
        List all wallets in the database.
        Args:
            db: Async database session.
        Returns:
            List[Wallet]: List of wallet instances.
        """
        result = await db.execute(select(Wallet))
        return result.scalars().all()

    @staticmethod
    async def delete(db: AsyncSession, address: str) -> bool:
        """
        Delete a wallet by its address.
        Args:
            db: Async database session.
            address: Wallet address to delete.
        Returns:
            bool: True if the wallet was deleted, False otherwise.
        """
        wallet = await WalletStore.get_by_address(db, address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        await db.delete(wallet)
        await db.commit()
        return True

    def delete_wallet(self, wallet_id: int) -> None:
        with self.Session() as session:
            session.query(Wallet).filter(Wallet.id == wallet_id).delete()
            session.commit()
