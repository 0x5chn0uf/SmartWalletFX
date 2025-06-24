from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.portfolio_snapshot_repository import (
    PortfolioSnapshotRepository,
)
from app.repositories.wallet_repository import WalletRepository
from app.schemas.portfolio_metrics import PortfolioMetrics
from app.schemas.portfolio_timeline import PortfolioTimeline
from app.schemas.wallet import WalletCreate, WalletResponse


class WalletUsecase:
    """
    Use case layer for wallet operations. Handles business logic for creating,
    listing, and deleting wallets, as well as portfolio-related operations.
    """

    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.user = current_user
        self.wallet_repository = WalletRepository(db)
        self.portfolio_snapshot_repository = PortfolioSnapshotRepository(db)

    async def create_wallet(self, wallet: WalletCreate) -> WalletResponse:
        """
        Create a new wallet using the provided database session and wallet
        data.
        Args:
            wallet: WalletCreate schema with wallet details.
        Returns:
            WalletResponse: The created wallet response object.
        """
        return await self.wallet_repository.create(
            address=wallet.address, user_id=self.user.id, name=wallet.name
        )

    async def list_wallets(self) -> List[WalletResponse]:
        """
        List all wallets from the database.
        Returns:
            List[WalletResponse]: List of wallet response objects.
        """
        return await self.wallet_repository.list_by_user(self.user.id)

    async def delete_wallet(self, address: str):
        """
        Delete a wallet by its address.
        Args:
            address: Wallet address to delete.
        """
        await self.wallet_repository.delete(address, user_id=self.user.id)

    async def verify_wallet_ownership(self, address: str) -> bool:
        """
        Verify that the current user owns the wallet.
        Args:
            address: Wallet address to verify.
        Returns:
            bool: True if the user owns the wallet, False otherwise.
        """
        wallet = await self.wallet_repository.get_by_address(address=address)
        return wallet is not None and wallet.user_id == self.user.id

    async def get_portfolio_snapshots(self, address: str) -> List[dict]:
        """
        Get portfolio snapshots for a wallet.
        Args:
            address: Wallet address to get snapshots for.
        Returns:
            List[dict]: List of portfolio snapshots.
        Raises:
            HTTPException: If wallet not found or user doesn't have permission.
        """
        if not await self.verify_wallet_ownership(address):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found or you do not have permission to view it.",
            )

        # Set default time range for last 30 days
        to_ts = int(datetime.utcnow().timestamp())
        from_ts = int((datetime.utcnow() - timedelta(days=30)).timestamp())

        return (
            await self.portfolio_snapshot_repository.get_snapshots_by_address_and_range(
                user_address=address, from_ts=from_ts, to_ts=to_ts
            )
        )

    async def get_portfolio_metrics(self, address: str) -> PortfolioMetrics:
        """
        Get portfolio metrics for a wallet.
        Args:
            address: Wallet address to get metrics for.
        Returns:
            PortfolioMetrics: Portfolio metrics for the wallet.
        Raises:
            HTTPException: If wallet not found or user doesn't have permission.
        """
        if not await self.verify_wallet_ownership(address):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found or you do not have permission to view it.",
            )

        from app.services.portfolio_service import PortfolioCalculationService

        service = PortfolioCalculationService(self.db)
        return await service.calculate_portfolio_metrics(user_address=address)

    async def get_portfolio_timeline(
        self, address: str, interval: str = "daily", limit: int = 30, offset: int = 0
    ) -> PortfolioTimeline:
        """
        Get portfolio timeline for a wallet.
        Args:
            address: Wallet address to get timeline for.
            interval: Time interval for aggregation.
            limit: Maximum number of snapshots to return.
            offset: Number of snapshots to skip.
        Returns:
            PortfolioTimeline: Portfolio timeline data.
        Raises:
            HTTPException: If wallet not found or user doesn't have permission.
        """
        if not await self.verify_wallet_ownership(address):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found or you do not have permission to view it.",
            )

        from app.services.portfolio_service import PortfolioCalculationService

        service = PortfolioCalculationService(self.db)
        return await service.calculate_portfolio_timeline(
            user_address=address,
            interval=interval,
            limit=limit,
            offset=offset,
        )
