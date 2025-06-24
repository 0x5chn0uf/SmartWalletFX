from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.token_balance_repository import TokenBalanceRepository
from app.schemas.token_balance import TokenBalanceCreate, TokenBalanceResponse


class TokenBalanceUsecase:
    """
    Use case layer for token balance operations. Handles business logic
    for creating and managing token balance records.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.token_balance_repository = TokenBalanceRepository(db)

    async def create_token_balance(
        self, tb: TokenBalanceCreate
    ) -> TokenBalanceResponse:
        """
        Create a new token balance record.
        Args:
            tb: TokenBalanceCreate schema with balance details.
        Returns:
            TokenBalanceResponse: The created token balance response object.
        """
        return await self.token_balance_repository.create(tb)
