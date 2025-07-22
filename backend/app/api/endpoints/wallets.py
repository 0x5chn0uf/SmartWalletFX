import time
from typing import List

from fastapi import APIRouter, Request, status

# Dependency imports
from app.api.dependencies import get_user_id_from_request
from app.domain.schemas.historical_balance import (
    HistoricalBalanceCreate,
    HistoricalBalanceResponse,
)
from app.domain.schemas.portfolio_metrics import PortfolioMetrics
from app.domain.schemas.portfolio_timeline import (
    PortfolioSnapshotResponse,
    PortfolioTimeline,
)
from app.domain.schemas.token import TokenCreate, TokenResponse
from app.domain.schemas.token_balance import (
    TokenBalanceCreate,
    TokenBalanceResponse,
)
from app.domain.schemas.token_price import TokenPriceCreate, TokenPriceResponse
from app.domain.schemas.wallet import WalletCreate, WalletResponse
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
    ):
        """Create a new wallet."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"

        # Get user_id from request (set by middleware)
        user_id = get_user_id_from_request(request)

        Audit.info(
            "Wallet creation started",
            user_id=user_id,
            wallet_address=wallet.address,
            wallet_name=wallet.name,
            client_ip=client_ip,
        )

        try:
            result = await Wallets.__wallet_uc.create_wallet(user_id, wallet)

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
    ):
        """List all wallets."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = get_user_id_from_request(request)

        Audit.info("Wallet listing started", user_id=user_id, client_ip=client_ip)

        try:
            result = await Wallets.__wallet_uc.list_wallets(user_id)

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
    ):
        """Delete a wallet by its address."""
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = get_user_id_from_request(request)

        Audit.info(
            "Wallet deletion started",
            user_id=str(user_id),
            wallet_address=address,
            client_ip=client_ip,
        )

        try:
            await Wallets.__wallet_uc.delete_wallet(user_id, address)

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
        request: Request,
        address: str,
    ):
        """Get portfolio snapshots for a wallet."""
        user_id = get_user_id_from_request(request)
        return await Wallets.__wallet_uc.get_portfolio_snapshots(user_id, address)

    @staticmethod
    @ep.get(
        "/wallets/{address}/portfolio/metrics",
        response_model=PortfolioMetrics,
    )
    async def get_portfolio_metrics(
        request: Request,
        address: str,
        interval: str = "daily",
    ):
        """Get portfolio metrics for a wallet."""
        user_id = get_user_id_from_request(request)
        return await Wallets.__wallet_uc.get_portfolio_metrics(user_id, address)

    @staticmethod
    @ep.get(
        "/wallets/{address}/portfolio/timeline",
        response_model=PortfolioTimeline,
    )
    async def get_portfolio_timeline(
        request: Request,
        address: str,
        interval: str = "daily",
        limit: int = 30,
        offset: int = 0,
    ):
        """Get portfolio timeline for a wallet."""
        user_id = get_user_id_from_request(request)
        return await Wallets.__wallet_uc.get_portfolio_timeline(
            user_id, address, interval, limit, offset
        )
