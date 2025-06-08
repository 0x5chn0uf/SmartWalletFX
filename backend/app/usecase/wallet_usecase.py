from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Wallet
from app.schemas.wallet import WalletCreate, WalletResponse
from app.stores.wallet_store import WalletStore


class WalletUsecase:
    @staticmethod
    def create_wallet(db: Session, wallet_data: WalletCreate) -> WalletResponse:
        if WalletStore.get_by_address(db, wallet_data.address):
            raise HTTPException(
                status_code=400, detail="Wallet address already exists."
            )
        # Validation EVM
        if not Wallet(address=wallet_data.address).validate_address():
            raise HTTPException(status_code=422, detail="Invalid EVM address.")
        return WalletStore.create(
            db, address=wallet_data.address, name=wallet_data.name
        )

    @staticmethod
    def list_wallets(db: Session) -> List[WalletResponse]:
        return WalletStore.list_all(db)

    @staticmethod
    def delete_wallet(db: Session, address: str) -> None:
        if not WalletStore.delete(db, address):
            raise HTTPException(status_code=404, detail="Wallet not found.")
