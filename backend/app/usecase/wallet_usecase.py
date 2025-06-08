from app.schemas.wallet import WalletCreate, WalletResponse
from app.stores.wallet_store import WalletStore


class WalletUsecase:
    @staticmethod
    def create_wallet(db, wallet: WalletCreate) -> WalletResponse:
        return WalletStore.create_wallet(db, wallet)

    @staticmethod
    def list_wallets(db) -> list[WalletResponse]:
        return WalletStore.list_wallets(db)

    @staticmethod
    def delete_wallet(db, address: str):
        WalletStore.delete_wallet(db, address)
