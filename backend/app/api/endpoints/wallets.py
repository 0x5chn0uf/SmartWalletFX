from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.wallet import WalletCreate, WalletResponse
from app.usecase.wallet_usecase import WalletUsecase

router = APIRouter()

db_dependency = Depends(get_db)


@router.post(
    "/wallets",
    response_model=WalletResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_wallet(
    wallet: WalletCreate, db: AsyncSession = db_dependency
):
    """
    Create a new wallet.
    Args:
        wallet: WalletCreate schema with wallet details.
        db: Async database session (dependency).
    Returns:
        WalletResponse: The created wallet response object.
    """
    return await WalletUsecase.create_wallet(db, wallet)


@router.get("/wallets", response_model=List[WalletResponse])
async def list_wallets(db: AsyncSession = db_dependency):
    """
    List all wallets.
    Args:
        db: Async database session (dependency).
    Returns:
        List[WalletResponse]: List of wallet response objects.
    """
    return await WalletUsecase.list_wallets(db)


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
    await WalletUsecase.delete_wallet(db, address)
    return None
