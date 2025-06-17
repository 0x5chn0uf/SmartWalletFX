from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.historical_balance_repository import (
    HistoricalBalanceRepository,
)
from app.repositories.token_balance_repository import TokenBalanceRepository
from app.repositories.token_price_repository import TokenPriceRepository
from app.repositories.token_repository import TokenRepository
from app.schemas.historical_balance import (
    HistoricalBalanceCreate,
    HistoricalBalanceResponse,
)
from app.schemas.token import TokenCreate, TokenResponse
from app.schemas.token_balance import TokenBalanceCreate, TokenBalanceResponse
from app.schemas.token_price import TokenPriceCreate, TokenPriceResponse
from app.schemas.wallet import WalletCreate, WalletResponse
from app.usecase.wallet_usecase import WalletUsecase

router = APIRouter()

db_dependency = Depends(get_db)


@router.post(
    "/wallets",
    response_model=WalletResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_wallet(wallet: WalletCreate, db: AsyncSession = db_dependency):
    """
    Create a new wallet.
    Args:
        wallet: WalletCreate schema with wallet details.
        db: Async database session (dependency).
    Returns:
        WalletResponse: The created wallet response object.
    """
    usecase = WalletUsecase(db)
    return await usecase.create_wallet(wallet)


@router.get("/wallets", response_model=List[WalletResponse])
async def list_wallets(db: AsyncSession = db_dependency):
    """
    List all wallets.
    Args:
        db: Async database session (dependency).
    Returns:
        List[WalletResponse]: List of wallet response objects.
    """
    usecase = WalletUsecase(db)
    return await usecase.list_wallets()


@router.delete("/wallets/{address}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wallet(address: str, db: AsyncSession = db_dependency):
    """
    Delete a wallet by its address.
    Args:
        address: Wallet address to delete.
        db: Async database session (dependency).
    Returns:
        None
    """
    usecase = WalletUsecase(db)
    await usecase.delete_wallet(address)
    return None


@router.post(
    "/tokens",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_token(token: TokenCreate, db: AsyncSession = db_dependency):
    return await TokenRepository(db).create(token)


@router.post(
    "/historical_balances",
    response_model=HistoricalBalanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_historical_balance(
    hb: HistoricalBalanceCreate, db: AsyncSession = db_dependency
):
    return await HistoricalBalanceRepository(db).create(hb)


@router.post(
    "/token_prices",
    response_model=TokenPriceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_token_price(tp: TokenPriceCreate, db: AsyncSession = db_dependency):
    return await TokenPriceRepository(db).create(tp)


@router.post(
    "/token_balances",
    response_model=TokenBalanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_token_balance(
    tb: TokenBalanceCreate, db: AsyncSession = db_dependency
):
    return await TokenBalanceRepository(db).create(tb)
