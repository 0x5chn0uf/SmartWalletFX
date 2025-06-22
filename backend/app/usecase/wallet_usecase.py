from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.wallet_repository import WalletRepository
from app.schemas.wallet import WalletCreate, WalletResponse


class WalletUsecase:
    """
    Use case layer for wallet operations. Handles business logic for creating,
    listing, and deleting wallets.
    """

    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.user = current_user
        self.wallet_repository = WalletRepository(db)

    async def create_wallet(self, wallet: WalletCreate) -> WalletResponse:
        """
        Create a new wallet using the provided database session and wallet
        data.
        Args:
            wallet: WalletCreate schema with wallet details.
        Returns:
            WalletResponse: The created wallet response object.
        """
        return await self.wallet_repository.create(
            address=wallet.address, user_id=self.user.id, name=wallet.name
        )

    async def list_wallets(self) -> list[WalletResponse]:
        """
        List all wallets from the database.
        Returns:
            List[WalletResponse]: List of wallet response objects.
        """
        return await self.wallet_repository.list_by_user(self.user.id)

    async def delete_wallet(self, address: str):
        """
        Delete a wallet by its address.
        Args:
            address: Wallet address to delete.
        """
        await self.wallet_repository.delete(address, user_id=self.user.id)
