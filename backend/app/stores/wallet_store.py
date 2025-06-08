from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Wallet


class WalletStore:
    @staticmethod
    def get_by_address(db: Session, address: str) -> Optional[Wallet]:
        return db.query(Wallet).filter(Wallet.address == address).first()

    @staticmethod
    def create(
        db: Session, address: str, name: Optional[str] = None
    ) -> Wallet:
        db_wallet = Wallet(address=address, name=name)
        db.add(db_wallet)
        db.commit()
        db.refresh(db_wallet)
        return db_wallet

    @staticmethod
    def list_all(db: Session) -> List[Wallet]:
        return db.query(Wallet).all()

    @staticmethod
    def delete(db: Session, address: str) -> bool:
        wallet = db.query(Wallet).filter(Wallet.address == address).first()
        if not wallet:
            return False
        db.delete(wallet)
        db.commit()
        return True
