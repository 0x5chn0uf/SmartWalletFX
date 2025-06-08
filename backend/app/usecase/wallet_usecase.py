from app.schemas.wallet import WalletCreate, WalletResponse
from app.stores.wallet_store import WalletStore


class WalletUsecase:
    """
    Use case layer for wallet operations. Handles business logic for creating,
    listing, and deleting wallets.
    """

    @staticmethod
    async def create_wallet(db, wallet: WalletCreate) -> WalletResponse:
        """
        Create a new wallet using the provided database session and wallet
        data.
        Args:
            db: Async database session.
            wallet: WalletCreate schema with wallet details.
        Returns:
            WalletResponse: The created wallet response object.
        """
        return await WalletStore.create(
            db, address=wallet.address, name=wallet.name
        )

    @staticmethod
    async def list_wallets(db) -> list[WalletResponse]:
        """
        List all wallets from the database.
        Args:
            db: Async database session.
        Returns:
            List[WalletResponse]: List of wallet response objects.
        """
        return await WalletStore.list_all(db)

    @staticmethod
    async def delete_wallet(db, address: str):
        """
        Delete a wallet by its address.
        Args:
            db: Async database session.
            address: Wallet address to delete.
        """
        await WalletStore.delete(db, address)
