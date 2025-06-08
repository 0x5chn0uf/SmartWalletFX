from app.schemas.wallet import WalletCreate, WalletResponse
from app.stores.wallet_store import WalletStore


class WalletUsecase:
    @staticmethod
    async def create_wallet(db, wallet: WalletCreate) -> WalletResponse:
        return await WalletStore.create(db, address=wallet.address, name=wallet.name)

    @staticmethod
    async def list_wallets(db) -> list[WalletResponse]:
        return await WalletStore.list_all(db)

    @staticmethod
    async def delete_wallet(db, address: str):
        await WalletStore.delete(db, address)
