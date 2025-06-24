from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.token_price_repository import TokenPriceRepository
from app.schemas.token_price import TokenPriceCreate, TokenPriceResponse


class TokenPriceUsecase:
    """
    Use case layer for token price operations. Handles business logic
    for creating and managing token price records.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.token_price_repository = TokenPriceRepository(db)

    async def create_token_price(self, tp: TokenPriceCreate) -> TokenPriceResponse:
        """
        Create a new token price record.
        Args:
            tp: TokenPriceCreate schema with price details.
        Returns:
            TokenPriceResponse: The created token price response object.
        """
        return await self.token_price_repository.create(tp)
