from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.wallet import WalletCreate, WalletResponse
from app.stores.wallet_store import WalletStore


class WalletUsecase:
    """
    Use case layer for wallet operations. Handles business logic for creating,
    listing, and deleting wallets.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_store = WalletStore(db)

    async def create_wallet(self, wallet: WalletCreate) -> WalletResponse:
        """
        Create a new wallet using the provided database session and wallet
        data.
        Args:
            wallet: WalletCreate schema with wallet details.
        Returns:
            WalletResponse: The created wallet response object.
        """
        return await self.wallet_store.create(address=wallet.address, name=wallet.name)

    async def list_wallets(self) -> list[WalletResponse]:
        """
        List all wallets from the database.
        Returns:
            List[WalletResponse]: List of wallet response objects.
        """
        return await self.wallet_store.list_all()

    async def delete_wallet(self, address: str):
        """
        Delete a wallet by its address.
        Args:
            address: Wallet address to delete.
        """
        await self.wallet_store.delete(address)
