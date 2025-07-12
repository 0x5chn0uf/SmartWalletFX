import time
from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import auth_deps
from app.core.database import get_db
from app.core.services import EndpointBase, ServiceContainer
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
from app.utils.logging import Audit


class Wallets(EndpointBase):
    """Class-based wallet endpoints."""

    ep = APIRouter(prefix="", tags=["wallets"])
    __container: ServiceContainer

    def __init__(self, container: ServiceContainer):
        super().__init__(container)
        Wallets.__container = container

    # ------------------------------------------------------------------
    # Wallet CRUD
    # ------------------------------------------------------------------
    @staticmethod
    @ep.post(
        "/wallets", response_model=WalletResponse, status_code=status.HTTP_201_CREATED
    )
    async def create_wallet(
        request: Request,
        wallet: WalletCreate,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(auth_deps.get_current_user),
    ) -> WalletResponse:
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
            usecase = Wallets.__container.usecases.WalletUsecase(db, current_user)
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
        except Exception as exc:  # pragma: no cover - passthrough
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
    @ep.get("/wallets", response_model=List[WalletResponse])
    async def list_wallets(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(auth_deps.get_current_user),
    ) -> List[WalletResponse]:
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        user_id = current_user.id
        Audit.info("Wallet listing started", user_id=user_id, client_ip=client_ip)
        try:
            usecase = Wallets.__container.usecases.WalletUsecase(db, current_user)
            result = await usecase.list_wallets()
            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "Wallet listing completed",
                user_id=str(user_id),
                wallet_count=len(result),
                duration_ms=duration,
            )
            return result
        except Exception as exc:  # pragma: no cover - passthrough
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
    @ep.delete("/wallets/{address}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_wallet(
        request: Request,
        address: str,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(auth_deps.get_current_user),
    ) -> None:
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
            usecase = Wallets.__container.usecases.WalletUsecase(db, current_user)
            await usecase.delete_wallet(address)
            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "Wallet deleted successfully",
                user_id=str(user_id),
                wallet_address=address,
                duration_ms=duration,
            )
            return None
        except Exception as exc:  # pragma: no cover - passthrough
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

    # ------------------------------------------------------------------
    # Related resources
    # ------------------------------------------------------------------
    @staticmethod
    @ep.post(
        "/tokens", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
    )
    async def create_token(
        token: TokenCreate, db: AsyncSession = Depends(get_db)
    ) -> TokenResponse:
        usecase = Wallets.__container.usecases.TokenUsecase(db)
        return await usecase.create_token(token)

    @staticmethod
    @ep.post(
        "/historical_balances",
        response_model=HistoricalBalanceResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_historical_balance(
        hb: HistoricalBalanceCreate, db: AsyncSession = Depends(get_db)
    ) -> HistoricalBalanceResponse:
        usecase = Wallets.__container.usecases.HistoricalBalanceUsecase(db)
        return await usecase.create_historical_balance(hb)

    @staticmethod
    @ep.post(
        "/token_prices",
        response_model=TokenPriceResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_token_price(
        tp: TokenPriceCreate, db: AsyncSession = Depends(get_db)
    ) -> TokenPriceResponse:
        usecase = Wallets.__container.usecases.TokenPriceUsecase(db)
        return await usecase.create_token_price(tp)

    @staticmethod
    @ep.post(
        "/token_balances",
        response_model=TokenBalanceResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_token_balance(
        tb: TokenBalanceCreate, db: AsyncSession = Depends(get_db)
    ) -> TokenBalanceResponse:
        usecase = Wallets.__container.usecases.TokenBalanceUsecase(db)
        return await usecase.create_token_balance(tb)

    @staticmethod
    @ep.get(
        "/wallets/{address}/portfolio/snapshots",
        response_model=List[PortfolioSnapshotResponse],
    )
    async def get_portfolio_snapshots(
        address: str,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(auth_deps.get_current_user),
    ) -> List[PortfolioSnapshotResponse]:
        usecase = Wallets.__container.usecases.WalletUsecase(db, current_user)
        return await usecase.get_portfolio_snapshots(address)

    @staticmethod
    @ep.get(
        "/wallets/{address}/portfolio/metrics",
        response_model=PortfolioMetrics,
    )
    async def get_portfolio_metrics(
        address: str,
        interval: str = "daily",
        db: AsyncSession = Depends(get_db),
        current_user=Depends(auth_deps.get_current_user),
    ) -> PortfolioMetrics:
        usecase = Wallets.__container.usecases.WalletUsecase(db, current_user)
        return await usecase.get_portfolio_metrics(address)

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
        db: AsyncSession = Depends(get_db),
        current_user=Depends(auth_deps.get_current_user),
    ) -> PortfolioTimeline:
        usecase = Wallets.__container.usecases.WalletUsecase(db, current_user)
        return await usecase.get_portfolio_timeline(
            address=address,
            interval=interval,
            limit=limit,
            offset=offset,
        )


# Factory ---------------------------------------------------------------


def get_router(container: ServiceContainer) -> APIRouter:
    Wallets(container)
    return Wallets.ep


router = get_router(ServiceContainer(load_celery=False))
