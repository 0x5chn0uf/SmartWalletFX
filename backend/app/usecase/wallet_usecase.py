import time
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException, status

from app.core.config import Configuration
from app.domain.schemas.portfolio_metrics import PortfolioMetrics
from app.domain.schemas.portfolio_timeline import PortfolioTimeline
from app.domain.schemas.wallet import WalletCreate, WalletResponse
from app.repositories.portfolio_snapshot_repository import (
    PortfolioSnapshotRepository,
)
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.utils.logging import Audit


class WalletUsecase:
    """
    Use case layer for wallet operations with explicit dependency injection.
    Handles business logic for creating, listing, and deleting wallets,
    as well as portfolio-related operations.
    """

    def __init__(
        self,
        wallet_repo: WalletRepository,
        user_repo: UserRepository,
        portfolio_snapshot_repo: PortfolioSnapshotRepository,
        config: Configuration,
        audit: Audit,
    ):
        self.__wallet_repo = wallet_repo
        self.__user_repo = user_repo
        self.__portfolio_snapshot_repo = portfolio_snapshot_repo
        self.__config_service = config
        self.__audit = audit

    async def create_wallet(
        self, user_id: uuid.UUID, wallet: WalletCreate
    ) -> WalletResponse:
        """
        Create a new wallet.
        Args:
            user_id: ID of the current user creating the wallet.
            wallet: WalletCreate schema with wallet details.
        Returns:
            WalletResponse: The created wallet response object.
        """
        start_time = time.time()

        # Verify user exists
        user = await self.__user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        self.__audit.info(
            "wallet_usecase_create_wallet_started",
            user_id=str(user_id),
            wallet_address=wallet.address,
            wallet_name=wallet.name,
        )

        try:
            result = await self.__wallet_repo.create(
                address=wallet.address, user_id=user_id, name=wallet.name
            )

            duration = int((time.time() - start_time) * 1000)
            self.__audit.info(
                "wallet_usecase_create_wallet_success",
                user_id=str(user_id),
                wallet_id=str(result.id),
                wallet_address=wallet.address,
                wallet_name=wallet.name,
                duration_ms=duration,
            )

            return result
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_usecase_create_wallet_failed",
                user_id=str(user_id),
                wallet_address=wallet.address,
                wallet_name=wallet.name,
                duration_ms=duration,
                error=str(exc),
            )
            raise

    async def list_wallets(self, user_id: uuid.UUID) -> List[WalletResponse]:
        """
        List all wallets from the database.
        Args:
            user_id: ID of the current user requesting wallets.
        Returns:
            List[WalletResponse]: List of wallet response objects.
        """
        start_time = time.time()

        # Verify user exists
        user = await self.__user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        self.__audit.info("wallet_usecase_list_wallets_started", user_id=str(user_id))

        try:
            result = await self.__wallet_repo.list_by_user(user_id)

            duration = int((time.time() - start_time) * 1000)
            self.__audit.info(
                "wallet_usecase_list_wallets_success",
                user_id=str(user_id),
                wallet_count=len(result),
                duration_ms=duration,
            )

            return result
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_usecase_list_wallets_failed",
                user_id=str(user_id),
                duration_ms=duration,
                error=str(exc),
            )
            raise

    async def delete_wallet(self, user_id: uuid.UUID, address: str):
        """
        Delete a wallet by its address.
        Args:
            user_id: ID of the current user deleting the wallet.
            address: Wallet address to delete.
        """
        start_time = time.time()

        # Verify user exists
        user = await self.__user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        self.__audit.info(
            "wallet_usecase_delete_wallet_started",
            user_id=str(user_id),
            wallet_address=address,
        )

        try:
            await self.__wallet_repo.delete(address, user_id=user_id)

            duration = int((time.time() - start_time) * 1000)
            self.__audit.info(
                "wallet_usecase_delete_wallet_success",
                user_id=str(user_id),
                wallet_address=address,
                duration_ms=duration,
            )
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_usecase_delete_wallet_failed",
                user_id=str(user_id),
                wallet_address=address,
                duration_ms=duration,
                error=str(exc),
            )
            raise

    async def verify_wallet_ownership(self, user_id: uuid.UUID, address: str) -> bool:
        """
        Verify that the current user owns the wallet.
        Args:
            user_id: ID of the current user to verify ownership for.
            address: Wallet address to verify.
        Returns:
            bool: True if the user owns the wallet, False otherwise.
        """
        start_time = time.time()

        # Verify user exists
        user = await self.__user_repo.get_by_id(user_id)
        if not user:
            return False

        self.__audit.info(
            "wallet_usecase_verify_ownership_started",
            user_id=str(user_id),
            wallet_address=address,
        )

        try:
            wallet = await self.__wallet_repo.get_by_address(address=address)
            is_owner = wallet is not None and wallet.user_id == user_id

            duration = int((time.time() - start_time) * 1000)
            self.__audit.info(
                "wallet_usecase_verify_ownership_success",
                user_id=str(user_id),
                wallet_address=address,
                is_owner=is_owner,
                duration_ms=duration,
            )

            return is_owner
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_usecase_verify_ownership_failed",
                user_id=str(user_id),
                wallet_address=address,
                duration_ms=duration,
                error=str(exc),
            )
            raise

    async def get_portfolio_snapshots(
        self, user_id: uuid.UUID, address: str
    ) -> List[dict]:
        """
        Get portfolio snapshots for a wallet.
        Args:
            user_id: ID of the current user requesting snapshots.
            address: Wallet address to get snapshots for.
        Returns:
            List[dict]: List of portfolio snapshots.
        """
        start_time = time.time()

        # Verify user exists
        user = await self.__user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        self.__audit.info(
            "wallet_usecase_get_portfolio_snapshots_started",
            user_id=str(user_id),
            wallet_address=address,
        )

        try:
            # Verify ownership first
            if not await self.verify_wallet_ownership(user_id, address):
                self.__audit.warning(
                    "wallet_usecase_get_portfolio_snapshots_unauthorized",
                    user_id=str(user_id),
                    wallet_address=address,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet not found or access denied",
                )

            snapshots = await self.__portfolio_snapshot_repo.get_by_wallet_address(
                address
            )

            duration = int((time.time() - start_time) * 1000)
            self.__audit.info(
                "wallet_usecase_get_portfolio_snapshots_success",
                user_id=str(user_id),
                wallet_address=address,
                snapshot_count=len(snapshots),
                duration_ms=duration,
            )

            return snapshots
        except HTTPException:
            raise
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_usecase_get_portfolio_snapshots_failed",
                user_id=str(user_id),
                wallet_address=address,
                duration_ms=duration,
                error=str(exc),
            )
            raise

    async def get_portfolio_metrics(
        self, user_id: uuid.UUID, address: str
    ) -> PortfolioMetrics:
        """
        Get portfolio metrics for a wallet.
        Args:
            user_id: ID of the current user requesting metrics.
            address: Wallet address to get metrics for.
        Returns:
            PortfolioMetrics: Portfolio metrics object.
        """
        start_time = time.time()

        # Verify user exists
        user = await self.__user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        self.__audit.info(
            "wallet_usecase_get_portfolio_metrics_started",
            user_id=str(user_id),
            wallet_address=address,
        )

        try:
            # Verify ownership first
            if not await self.verify_wallet_ownership(user_id, address):
                self.__audit.warning(
                    "wallet_usecase_get_portfolio_metrics_unauthorized",
                    user_id=str(user_id),
                    wallet_address=address,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet not found or access denied",
                )

            # Get latest snapshot
            snapshots = await self.__portfolio_snapshot_repo.get_by_wallet_address(
                address
            )
            if not snapshots:
                self.__audit.warning(
                    "wallet_usecase_get_portfolio_metrics_no_snapshots",
                    user_id=str(user_id),
                    wallet_address=address,
                )
                # Return empty metrics instead of raising an error

                metrics = PortfolioMetrics(
                    user_address=address,
                    total_collateral=0.0,
                    total_borrowings=0.0,
                    total_collateral_usd=0.0,
                    total_borrowings_usd=0.0,
                    aggregate_health_score=None,
                    aggregate_apy=None,
                    collaterals=[],
                    borrowings=[],
                    staked_positions=[],
                    health_scores=[],
                    protocol_breakdown={},
                    timestamp=datetime.now(),
                )
            else:
                # Get the most recent snapshot (assuming the first one is the latest)
                snapshot = snapshots[0]
                metrics = PortfolioMetrics(
                    user_address=address,
                    total_collateral=snapshot.get("total_collateral", 0.0),
                    total_borrowings=snapshot.get("total_borrowings", 0.0),
                    total_collateral_usd=snapshot.get("total_collateral_usd", 0.0),
                    total_borrowings_usd=snapshot.get("total_borrowings_usd", 0.0),
                    aggregate_health_score=snapshot.get("aggregate_health_score"),
                    aggregate_apy=snapshot.get("aggregate_apy"),
                    collaterals=snapshot.get("collaterals", []),
                    borrowings=snapshot.get("borrowings", []),
                    staked_positions=snapshot.get("staked_positions", []),
                    health_scores=snapshot.get("health_scores", []),
                    protocol_breakdown=snapshot.get("protocol_breakdown", {}),
                    timestamp=snapshot.get("timestamp", datetime.now()),
                )

            duration = int((time.time() - start_time) * 1000)
            self.__audit.info(
                "wallet_usecase_get_portfolio_metrics_success",
                user_id=str(user_id),
                wallet_address=address,
                total_collateral_usd=metrics.total_collateral_usd,
                total_borrowings_usd=metrics.total_borrowings_usd,
                duration_ms=duration,
            )

            return metrics
        except HTTPException:
            raise
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_usecase_get_portfolio_metrics_failed",
                user_id=str(user_id),
                wallet_address=address,
                duration_ms=duration,
                error=str(exc),
            )
            raise

    async def get_portfolio_timeline(
        self,
        user_id: uuid.UUID,
        address: str,
        interval: str = "daily",
        limit: int = 30,
        offset: int = 0,
    ) -> PortfolioTimeline:
        """
        Get portfolio timeline for a wallet.
        Args:
            user_id: ID of the current user requesting timeline.
            address: Wallet address to get timeline for.
            interval: Time interval for the timeline.
            limit: Maximum number of data points to return.
            offset: Number of data points to skip.
        Returns:
            PortfolioTimeline: Portfolio timeline object.
        """
        start_time = time.time()

        # Verify user exists
        user = await self.__user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        self.__audit.info(
            "wallet_usecase_get_portfolio_timeline_started",
            user_id=str(user_id),
            wallet_address=address,
            interval=interval,
            limit=limit,
            offset=offset,
        )

        try:
            # Verify ownership first
            if not await self.verify_wallet_ownership(user_id, address):
                self.__audit.warning(
                    "wallet_usecase_get_portfolio_timeline_unauthorized",
                    user_id=str(user_id),
                    wallet_address=address,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet not found or access denied",
                )

            # Get timeline data
            # Calculate default time range (last 30 days)
            to_ts = int(datetime.now().timestamp())
            from_ts = int((datetime.now() - timedelta(days=30)).timestamp())

            timeline_data = await self.__portfolio_snapshot_repo.get_timeline(
                address, from_ts, to_ts, limit, offset, interval
            )

            # Transform data into PortfolioTimeline format
            timestamps = []
            collateral_usd = []
            borrowings_usd = []

            for snapshot in timeline_data:
                timestamps.append(int(snapshot.timestamp))
                collateral_usd.append(float(snapshot.total_collateral_usd or 0.0))
                borrowings_usd.append(float(snapshot.total_borrowings_usd or 0.0))

            timeline = PortfolioTimeline(
                timestamps=timestamps,
                collateral_usd=collateral_usd,
                borrowings_usd=borrowings_usd,
            )

            duration = int((time.time() - start_time) * 1000)
            self.__audit.info(
                "wallet_usecase_get_portfolio_timeline_success",
                user_id=str(user_id),
                wallet_address=address,
                interval=interval,
                data_points=len(timeline_data),
                duration_ms=duration,
            )

            return timeline
        except HTTPException:
            raise
        except Exception as exc:
            duration = int((time.time() - start_time) * 1000)
            self.__audit.error(
                "wallet_usecase_get_portfolio_timeline_failed",
                user_id=str(user_id),
                wallet_address=address,
                interval=interval,
                duration_ms=duration,
                error=str(exc),
            )
            raise
