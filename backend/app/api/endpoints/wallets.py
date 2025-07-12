import time
from typing import List

from fastapi import APIRouter, Depends, Request, status

# Dependency imports
from app.api.dependencies import auth_deps
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
from app.usecase.portfolio_snapshot_usecase import PortfolioSnapshotUsecase
from app.usecase.token_balance_usecase import TokenBalanceUsecase
from app.usecase.token_price_usecase import TokenPriceUsecase
from app.usecase.token_usecase import TokenUsecase
from app.usecase.wallet_usecase import WalletUsecase
from app.utils.logging import Audit


class Wallets:
    """Wallets endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(tags=["wallets"])
    __wallet_uc: WalletUsecase
    __token_uc: TokenUsecase
    __historical_balance_uc: HistoricalBalanceUsecase
    __token_price_uc: TokenPriceUsecase
    __token_balance_uc: TokenBalanceUsecase
    __portfolio_snapshot_uc: PortfolioSnapshotUsecase

    def __init__(
        self,
        wallet_usecase: WalletUsecase,
        token_usecase: TokenUsecase,
        historical_balance_usecase: HistoricalBalanceUsecase,
        token_price_usecase: TokenPriceUsecase,
        token_balance_usecase: TokenBalanceUsecase,
        portfolio_snapshot_usecase: PortfolioSnapshotUsecase,
    ):
        """Initialize with injected dependencies."""
        Wallets.__wallet_uc = wallet_usecase
        Wallets.__token_uc = token_usecase
        Wallets.__historical_balance_uc = historical_balance_usecase
        Wallets.__token_price_uc = token_price_usecase
        Wallets.__token_balance_uc = token_balance_usecase
        Wallets.__portfolio_snapshot_uc = portfolio_snapshot_usecase

    @staticmethod
    @ep.post(
        "/wallets",
        response_model=WalletResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_wallet(
        request: Request,
        wallet: WalletCreate,
        current_user=Depends(auth_deps.get_current_user),
    ):
        """Create a new wallet."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = current_user.id

        Audit.info(
            "Wallet creation started",
            user_id=user_id,
            wallet_address=wallet.address,
            wallet_name=wallet.name,
            client_ip=client_ip,
        )

        try:
            result = await Wallets.__wallet_uc.create_wallet(current_user, wallet)

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

    @staticmethod
    @ep.get(
        "/wallets",
        response_model=List[WalletResponse],
    )
    async def list_wallets(
        request: Request,
        current_user=Depends(auth_deps.get_current_user),
    ):
        """List all wallets."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = current_user.id

        Audit.info("Wallet listing started", user_id=user_id, client_ip=client_ip)

        try:
            result = await Wallets.__wallet_uc.list_wallets(current_user)

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

    @staticmethod
    @ep.delete(
        "/wallets/{address}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_wallet(
        request: Request,
        address: str,
        current_user=Depends(auth_deps.get_current_user),
    ):
        """Delete a wallet by its address."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = current_user.id

        Audit.info(
            "Wallet deletion started",
            user_id=str(user_id),
            wallet_address=address,
            client_ip=client_ip,
        )

        try:
            await Wallets.__wallet_uc.delete_wallet(current_user, address)

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

    @staticmethod
    @ep.post(
        "/tokens",
        response_model=TokenResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_token(token: TokenCreate):
        """Create a new token."""
        return await Wallets.__token_uc.create_token(token)

    @staticmethod
    @ep.post(
        "/historical_balances",
        response_model=HistoricalBalanceResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_historical_balance(hb: HistoricalBalanceCreate):
        """Create a new historical balance."""
        return await Wallets.__historical_balance_uc.create_historical_balance(hb)

    @staticmethod
    @ep.post(
        "/token_prices",
        response_model=TokenPriceResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_token_price(tp: TokenPriceCreate):
        """Create a new token price."""
        return await Wallets.__token_price_uc.create_token_price(tp)

    @staticmethod
    @ep.post(
        "/token_balances",
        response_model=TokenBalanceResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_token_balance(tb: TokenBalanceCreate):
        """Create a new token balance."""
        return await Wallets.__token_balance_uc.create_token_balance(tb)

    @staticmethod
    @ep.get(
        "/wallets/{address}/portfolio/snapshots",
        response_model=List[PortfolioSnapshotResponse],
    )
    async def get_portfolio_snapshots(
        address: str,
        current_user=Depends(auth_deps.get_current_user),
    ):
        """Get portfolio snapshots for a wallet."""
        return await Wallets.__portfolio_snapshot_uc.get_portfolio_snapshots(
            current_user, address
        )

    @staticmethod
    @ep.get(
        "/wallets/{address}/portfolio/metrics",
        response_model=PortfolioMetrics,
    )
    async def get_portfolio_metrics(
        address: str,
        interval: str = "daily",
        current_user=Depends(auth_deps.get_current_user),
    ):
        """Get portfolio metrics for a wallet."""
        return await Wallets.__portfolio_snapshot_uc.get_portfolio_metrics(
            current_user, address, interval
        )

    @staticmethod
    @ep.get(
        "/wallets/{address}/portfolio/timeline",
        response_model=PortfolioTimeline,
    )
    async def get_portfolio_timeline(
        address: str,
        interval: str = "daily",
        limit: int = 30,
        offset: int = 0,
        current_user=Depends(auth_deps.get_current_user),
    ):
        """Get portfolio timeline for a wallet."""
        return await Wallets.__portfolio_snapshot_uc.get_portfolio_timeline(
            current_user, address, interval, limit, offset
        )


# Backward compatibility - create router instance and old class
# This will be replaced when main.py is updated to use DIContainer
class WalletView:
    """Class-based view for wallet endpoints."""

    def __init__(self):
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self):
        """Register all wallet-related routes."""
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.core.database import get_db

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
            """Create a new wallet."""
            start_time = time.time()
            client_ip = request.client.host or "unknown"
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

        # Add other legacy endpoints here...


# Create router instance for backward compatibility
wallet_view = WalletView()
router = wallet_view.router
