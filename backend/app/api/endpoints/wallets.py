import time
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

# Dependency imports
from app.api.dependencies import auth_deps
from app.core.database import get_db
from app.schemas.historical_balance import (
    HistoricalBalanceCreate,
    HistoricalBalanceResponse,
)
from app.schemas.portfolio_metrics import PortfolioMetrics
from app.schemas.portfolio_timeline import (
    PortfolioSnapshotResponse,
    PortfolioTimeline,
)
from app.schemas.token import TokenCreate, TokenResponse
from app.schemas.token_balance import TokenBalanceCreate, TokenBalanceResponse
from app.schemas.token_price import TokenPriceCreate, TokenPriceResponse
from app.schemas.wallet import WalletCreate, WalletResponse
from app.usecase.historical_balance_usecase import HistoricalBalanceUsecase
from app.usecase.token_balance_usecase import TokenBalanceUsecase
from app.usecase.token_price_usecase import TokenPriceUsecase
from app.usecase.token_usecase import TokenUsecase
from app.usecase.wallet_usecase import WalletUsecase
from app.utils.logging import Audit


class WalletView:
    """Class-based view for wallet endpoints."""

    def __init__(self):
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self):
        """Register all wallet-related routes."""

        @self.router.post(
            "/wallets",
            response_model=WalletResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_wallet(
            request: Request,
            wallet: WalletCreate,
            db: AsyncSession = Depends(get_db),
            current_user=Depends(auth_deps.get_current_user),
        ):
            """
            Create a new wallet.
            Args:
                wallet: WalletCreate schema with wallet details.
                db: Async database session (dependency).
                current_user: Current authenticated user (dependency).
            Returns:
                WalletResponse: The created wallet response object.
            """
            start_time = time.time()
            client_ip = request.client.host or "unknown"

            # Cache user_id early to avoid greenlet issues in exception handling
            user_id = current_user.id

            Audit.info(
                "Wallet creation started",
                user_id=user_id,
                wallet_address=wallet.address,
                wallet_name=wallet.name,
                client_ip=client_ip,
            )

            try:
                usecase = WalletUsecase(db, current_user)
                result = await usecase.create_wallet(wallet)

                duration = int((time.time() - start_time) * 1000)
                Audit.info(
                    "Wallet created successfully",
                    user_id=user_id,
                    wallet_id=str(result.id),
                    wallet_address=wallet.address,
                    wallet_name=wallet.name,
                    duration_ms=duration,
                )

                return result
            except Exception as exc:
                duration = int((time.time() - start_time) * 1000)
                Audit.error(
                    "Wallet creation failed",
                    user_id=user_id,
                    wallet_address=wallet.address,
                    wallet_name=wallet.name,
                    duration_ms=duration,
                    error=str(exc),
                    exc_info=True,
                )
                raise

        @self.router.get(
            "/wallets",
            response_model=List[WalletResponse],
        )
        async def list_wallets(
            request: Request,
            db: AsyncSession = Depends(get_db),
            current_user=Depends(auth_deps.get_current_user),
        ):
            """
            List all wallets.
            Args:
                db: Async database session (dependency).
                current_user: Current authenticated user (dependency).
            Returns:
                List[WalletResponse]: List of wallet response objects.
            """
            start_time = time.time()
            client_ip = request.client.host or "unknown"

            # Cache user_id early to avoid greenlet issues in exception handling
            user_id = current_user.id

            Audit.info("Wallet listing started", user_id=user_id, client_ip=client_ip)

            try:
                usecase = WalletUsecase(db, current_user)
                result = await usecase.list_wallets()

                duration = int((time.time() - start_time) * 1000)
                Audit.info(
                    "Wallet listing completed",
                    user_id=str(user_id),
                    wallet_count=len(result),
                    duration_ms=duration,
                )

                return result
            except Exception as exc:
                duration = int((time.time() - start_time) * 1000)
                Audit.error(
                    "Wallet listing failed",
                    user_id=str(user_id),
                    duration_ms=duration,
                    error=str(exc),
                    exc_info=True,
                )
                raise

        @self.router.delete(
            "/wallets/{address}",
            status_code=status.HTTP_204_NO_CONTENT,
        )
        async def delete_wallet(
            request: Request,
            address: str,
            db: AsyncSession = Depends(get_db),
            current_user=Depends(auth_deps.get_current_user),
        ):
            """
            Delete a wallet by its address.
            Args:
                address: Wallet address to delete.
                db: Async database session (dependency).
                current_user: Current authenticated user (dependency).
            Returns:
                None
            """
            start_time = time.time()
            client_ip = request.client.host or "unknown"

            # Cache user_id early to avoid greenlet issues in exception handling
            user_id = current_user.id

            Audit.info(
                "Wallet deletion started",
                user_id=str(user_id),
                wallet_address=address,
                client_ip=client_ip,
            )

            try:
                usecase = WalletUsecase(db, current_user)
                await usecase.delete_wallet(address)

                duration = int((time.time() - start_time) * 1000)
                Audit.info(
                    "Wallet deleted successfully",
                    user_id=str(user_id),
                    wallet_address=address,
                    duration_ms=duration,
                )

                return None
            except Exception as exc:
                duration = int((time.time() - start_time) * 1000)
                Audit.error(
                    "Wallet deletion failed",
                    user_id=str(user_id),
                    wallet_address=address,
                    duration_ms=duration,
                    error=str(exc),
                    exc_info=True,
                )
                raise

        @self.router.post(
            "/tokens",
            response_model=TokenResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_token(token: TokenCreate, db: AsyncSession = Depends(get_db)):
            """Create a new token."""
            usecase = TokenUsecase(db)
            return await usecase.create_token(token)

        @self.router.post(
            "/historical_balances",
            response_model=HistoricalBalanceResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_historical_balance(
            hb: HistoricalBalanceCreate, db: AsyncSession = Depends(get_db)
        ):
            """Create a new historical balance record."""
            usecase = HistoricalBalanceUsecase(db)
            return await usecase.create_historical_balance(hb)

        @self.router.post(
            "/token_prices",
            response_model=TokenPriceResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_token_price(
            tp: TokenPriceCreate, db: AsyncSession = Depends(get_db)
        ):
            """Create a new token price record."""
            usecase = TokenPriceUsecase(db)
            return await usecase.create_token_price(tp)

        @self.router.post(
            "/token_balances",
            response_model=TokenBalanceResponse,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_token_balance(
            tb: TokenBalanceCreate, db: AsyncSession = Depends(get_db)
        ):
            """Create a new token balance record."""
            usecase = TokenBalanceUsecase(db)
            return await usecase.create_token_balance(tb)

        @self.router.get(
            "/wallets/{address}/portfolio/snapshots",
            response_model=List[PortfolioSnapshotResponse],
        )
        async def get_portfolio_snapshots(
            address: str,
            db: AsyncSession = Depends(get_db),
            current_user=Depends(auth_deps.get_current_user),
        ):
            """
            Retrieve portfolio snapshots for a given wallet address.
            """
            usecase = WalletUsecase(db, current_user)
            return await usecase.get_portfolio_snapshots(address)

        @self.router.get(
            "/wallets/{address}/portfolio/metrics",
            response_model=PortfolioMetrics,
        )
        async def get_portfolio_metrics(
            address: str,
            interval: str = "daily",
            db: AsyncSession = Depends(get_db),
            current_user=Depends(auth_deps.get_current_user),
        ):
            """Retrieve aggregated portfolio metrics for a wallet."""
            usecase = WalletUsecase(db, current_user)
            return await usecase.get_portfolio_metrics(address)

        @self.router.get(
            "/wallets/{address}/portfolio/timeline",
            response_model=PortfolioTimeline,
        )
        async def get_portfolio_timeline(
            address: str,
            interval: str = "daily",
            limit: int = 30,
            offset: int = 0,
            db: AsyncSession = Depends(get_db),
            current_user=Depends(auth_deps.get_current_user),
        ):
            """Retrieve historical portfolio trend data for visualization."""
            usecase = WalletUsecase(db, current_user)
            return await usecase.get_portfolio_timeline(
                address=address,
                interval=interval,
                limit=limit,
                offset=offset,
            )


# Create view instance and export router
wallet_view = WalletView()
router = wallet_view.router
