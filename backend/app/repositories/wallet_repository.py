import time
import uuid
from typing import List, Optional

import structlog
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet

logger = structlog.get_logger(__name__)


class WalletRepository:
    """Repository layer for wallet persistence operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    async def get_by_address(self, address: str) -> Optional[Wallet]:
        start_time = time.time()

        logger.debug("Querying wallet by address", address=address)

        try:
            result = await self.db.execute(
                select(Wallet).where(Wallet.address == address)
            )
            wallet = result.scalars().first()

            duration = int((time.time() - start_time) * 1000)
            logger.debug(
                "Wallet query completed",
                address=address,
                found=wallet is not None,
                duration_ms=duration,
            )

            return wallet
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            logger.error(
                "Wallet query failed",
                address=address,
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

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
        start_time = time.time()

        logger.info(
            "Creating wallet in database", address=address, user_id=user_id, name=name
        )

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

            duration = int((time.time() - start_time) * 1000)
            logger.info(
                "Wallet created successfully in database",
                wallet_id=db_wallet.id,
                address=address,
                user_id=user_id,
                name=name,
                duration_ms=duration,
            )

            return db_wallet
        except IntegrityError as exc:
            await self.db.rollback()
            duration = int((time.time() - start_time) * 1000)
            logger.warning(
                "Wallet creation failed - duplicate address",
                address=address,
                user_id=user_id,
                name=name,
                duration_ms=duration,
                error=str(exc),
            )
            raise HTTPException(status_code=400, detail="Wallet address already exists")
        except Exception as exc:
            await self.db.rollback()
            duration = int((time.time() - start_time) * 1000)
            logger.error(
                "Database error during wallet creation",
                address=address,
                user_id=user_id,
                name=name,
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

    async def list_by_user(self, user_id: uuid.UUID) -> List[Wallet]:
        """Return wallets owned by *user_id*."""
        start_time = time.time()

        logger.debug("Querying wallets by user", user_id=user_id)

        try:
            result = await self.db.execute(
                select(Wallet).where(Wallet.user_id == user_id)
            )
            wallets = result.scalars().all()

            duration = int((time.time() - start_time) * 1000)
            logger.debug(
                "Wallets query completed",
                user_id=user_id,
                wallet_count=len(wallets),
                duration_ms=duration,
            )

            return wallets
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            logger.error(
                "Wallets query failed",
                user_id=user_id,
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

    async def delete(self, address: str, user_id: uuid.UUID) -> bool:
        """Delete wallet.

        Args:
            address: Wallet address to delete.
            user_id: Owner user ID (required for authorization).
        """
        start_time = time.time()

        logger.info("Deleting wallet from database", address=address, user_id=user_id)

        try:
            wallet = await self.get_by_address(address)
            if not wallet:
                duration = int((time.time() - start_time) * 1000)
                logger.warning(
                    "Wallet deletion failed - not found",
                    address=address,
                    user_id=user_id,
                    duration_ms=duration,
                )
                raise HTTPException(status_code=404, detail="Wallet not found")

            if wallet.user_id != user_id:
                duration = int((time.time() - start_time) * 1000)
                logger.warning(
                    "Wallet deletion failed - unauthorized",
                    address=address,
                    user_id=user_id,
                    wallet_owner_id=wallet.user_id,
                    duration_ms=duration,
                )
                raise HTTPException(status_code=404, detail="Wallet not found")

            await self.db.delete(wallet)
            await self.db.commit()

            duration = int((time.time() - start_time) * 1000)
            logger.info(
                "Wallet deleted successfully from database",
                address=address,
                user_id=user_id,
                duration_ms=duration,
            )

            return True
        except HTTPException:
            raise
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            logger.error(
                "Database error during wallet deletion",
                address=address,
                user_id=user_id,
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise
