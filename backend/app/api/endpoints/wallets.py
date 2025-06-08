from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

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
def create_wallet(wallet: WalletCreate, db: Session = db_dependency):
    return WalletUsecase.create_wallet(db, wallet)


@router.get("/wallets", response_model=List[WalletResponse])
def list_wallets(db: Session = db_dependency):
    return WalletUsecase.list_wallets(db)


@router.delete("/wallets/{address}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wallet(address: str, db: Session = db_dependency):
    WalletUsecase.delete_wallet(db, address)
    return None
