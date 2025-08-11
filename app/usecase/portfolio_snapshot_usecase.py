import json

from fastapi import HTTPException

from app.domain.schemas.defi import PortfolioSnapshot
from app.repositories.portfolio_snapshot_repository import (
    PortfolioSnapshotRepository,
)
from app.repositories.wallet_repository import WalletRepository
from app.utils.logging import Audit


class PortfolioSnapshotUsecase:
    """
    Use case layer for portfolio snapshot operations with explicit dependency injection.
    Handles business logic for creating and managing portfolio snapshot records.
    """

    def __init__(
        self,
        portfolio_snapshot_repo: PortfolioSnapshotRepository,
        wallet_repo: WalletRepository,
        audit: Audit,
    ):
        self.__portfolio_snapshot_repo = portfolio_snapshot_repo
        self.__wallet_repo = wallet_repo
        self.__audit = audit

    async def get_snapshots_by_wallet(self, wallet_address: str) -> list[dict]:
        """
        Get portfolio snapshots for a specific wallet.
        Args:
            wallet_address: The wallet address to get snapshots for.
        Returns:
            list[dict]: List of portfolio snapshots.
        Raises:
            HTTPException: 404 if wallet does not exist.
        """
        self.__audit.info(
            "portfolio_snapshot_usecase_get_by_wallet_started",
            wallet_address=wallet_address,
        )

        try:
            # First, check if the wallet exists
            wallet = await self.__wallet_repo.get_by_address(wallet_address)
            if not wallet:
                self.__audit.warning(
                    "portfolio_snapshot_usecase_wallet_not_found",
                    wallet_address=wallet_address,
                )
                raise HTTPException(status_code=404, detail="Wallet not found")

            result = await self.__portfolio_snapshot_repo.get_by_wallet_address(
                wallet_address
            )

            self.__audit.info(
                "portfolio_snapshot_usecase_get_by_wallet_success",
                wallet_address=wallet_address,
                snapshot_count=len(result),
            )

            return result
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_usecase_get_by_wallet_failed",
                wallet_address=wallet_address,
                error=str(e),
            )
            raise

    async def get_timeline(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        limit: int = 100,
        offset: int = 0,
        interval: str = "none",
    ) -> list[PortfolioSnapshot]:
        """
        Fetch portfolio snapshots for a user address within a
        given timestamp range, with pagination and interval aggregation.
        Uses database cache for performance.
        """
        self.__audit.info(
            "portfolio_snapshot_usecase_get_timeline_started",
            user_address=user_address,
            from_ts=from_ts,
            to_ts=to_ts,
            interval=interval,
            limit=limit,
            offset=offset,
        )

        try:
            # Try cache
            cached = await self.__portfolio_snapshot_repo.get_cache(
                user_address, from_ts, to_ts, interval, limit, offset
            )
            if cached:
                cached_data = [PortfolioSnapshot(**obj) for obj in json.loads(cached)]
                self.__audit.info(
                    "portfolio_snapshot_usecase_get_timeline_cache_hit",
                    user_address=user_address,
                    snapshot_count=len(cached_data),
                )
                return cached_data

            # Compute result
            result = await self.__portfolio_snapshot_repo.get_timeline(
                user_address, from_ts, to_ts, limit, offset, interval
            )
            # Convert to Pydantic models
            pydantic_result = [
                PortfolioSnapshot.model_validate(r, from_attributes=True)
                for r in result
            ]

            # Cache the result as list of dicts
            await self.__portfolio_snapshot_repo.set_cache(
                user_address=user_address,
                from_ts=from_ts,
                to_ts=to_ts,
                interval=interval,
                limit=limit,
                offset=offset,
                response_json=json.dumps([p.model_dump() for p in pydantic_result]),
            )

            self.__audit.info(
                "portfolio_snapshot_usecase_get_timeline_success",
                user_address=user_address,
                snapshot_count=len(pydantic_result),
            )

            return pydantic_result
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_usecase_get_timeline_failed",
                user_address=user_address,
                error=str(e),
            )
            raise
