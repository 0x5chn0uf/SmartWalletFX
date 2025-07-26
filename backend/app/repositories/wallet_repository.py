import time
import uuid
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import CoreDatabase
from app.domain.interfaces.repositories import WalletRepositoryInterface
from app.models import Wallet
from app.utils.logging import Audit


class WalletRepository(WalletRepositoryInterface):
    """Repository layer for wallet persistence operations."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def get_by_address(self, address: str) -> Optional[Wallet]:
        """Get wallet by address."""
        start_time = time.time()
        self.__audit.info("wallet_repository_get_by_address_started", address=address)

        try:
            async with self.__database.get_session() as session:
                result = await session.execute(
                    select(Wallet).where(Wallet.address == address)
                )
                wallet = result.scalars().first()

                duration = int((time.time() - start_time) * 1000)
                self.__audit.info(
                    "wallet_repository_get_by_address_success",
                    address=address,
                    found=wallet is not None,
                    duration_ms=duration,
                )

                return wallet
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_repository_get_by_address_failed",
                address=address,
                duration_ms=duration,
                error=str(exc),
            )
            raise

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
        self.__audit.info(
            "wallet_repository_create_started",
            address=address,
            user_id=str(user_id),
            name=name,
        )

        try:
            async with self.__database.get_session() as session:
                db_wallet = Wallet(
                    user_id=user_id,
                    address=address,
                    name=name or "Unnamed Wallet",
                    balance_usd=0.0,
                )
                session.add(db_wallet)

                try:
                    await session.commit()
                    await session.refresh(db_wallet)

                    duration = int((time.time() - start_time) * 1000)
                    self.__audit.info(
                        "wallet_repository_create_success",
                        wallet_id=str(db_wallet.id),
                        address=address,
                        user_id=str(user_id),
                        name=name,
                        duration_ms=duration,
                    )

                    return db_wallet
                except IntegrityError as exc:
                    await session.rollback()
                    duration = int((time.time() - start_time) * 1000)
                    self.__audit.warning(
                        "wallet_repository_create_duplicate",
                        address=address,
                        user_id=str(user_id),
                        name=name,
                        duration_ms=duration,
                        error=str(exc),
                    )
                    raise HTTPException(
                        status_code=400, detail="Wallet address already exists"
                    )
        except HTTPException:
            raise
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_repository_create_failed",
                address=address,
                user_id=str(user_id),
                name=name,
                duration_ms=duration,
                error=str(exc),
            )
            raise

    async def list_by_user(self, user_id: uuid.UUID) -> List[Wallet]:
        """Return wallets owned by *user_id*."""
        start_time = time.time()
        self.__audit.info(
            "wallet_repository_list_by_user_started", user_id=str(user_id)
        )

        try:
            async with self.__database.get_session() as session:
                result = await session.execute(
                    select(Wallet).where(Wallet.user_id == user_id)
                )
                wallets = result.scalars().all()

                duration = int((time.time() - start_time) * 1000)
                self.__audit.info(
                    "wallet_repository_list_by_user_success",
                    user_id=str(user_id),
                    wallet_count=len(wallets),
                    duration_ms=duration,
                )

                return wallets
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_repository_list_by_user_failed",
                user_id=str(user_id),
                duration_ms=duration,
                error=str(exc),
            )
            raise

    async def delete(self, address: str, user_id: uuid.UUID) -> bool:
        """Delete wallet.

        Args:
            address: Wallet address to delete.
            user_id: Owner user ID (required for authorization).
        """
        start_time = time.time()
        self.__audit.info(
            "wallet_repository_delete_started",
            address=address,
            user_id=str(user_id),
        )

        try:
            async with self.__database.get_session() as session:
                # Get the wallet first
                result = await session.execute(
                    select(Wallet).where(Wallet.address == address)
                )
                wallet = result.scalars().first()

                if not wallet:
                    duration = int((time.time() - start_time) * 1000)
                    self.__audit.warning(
                        "wallet_repository_delete_not_found",
                        address=address,
                        user_id=str(user_id),
                        duration_ms=duration,
                    )
                    raise HTTPException(status_code=404, detail="Wallet not found")

                if wallet.user_id != user_id:
                    duration = int((time.time() - start_time) * 1000)
                    self.__audit.warning(
                        "wallet_repository_delete_unauthorized",
                        address=address,
                        user_id=str(user_id),
                        wallet_owner_id=str(wallet.user_id),
                        duration_ms=duration,
                    )
                    raise HTTPException(status_code=404, detail="Wallet not found")

                await session.delete(wallet)
                await session.commit()

                duration = int((time.time() - start_time) * 1000)
                self.__audit.info(
                    "wallet_repository_delete_success",
                    address=address,
                    user_id=str(user_id),
                    duration_ms=duration,
                )

                return True
        except HTTPException:
            raise
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_repository_delete_failed",
                address=address,
                user_id=str(user_id),
                duration_ms=duration,
                error=str(exc),
            )
            raise
