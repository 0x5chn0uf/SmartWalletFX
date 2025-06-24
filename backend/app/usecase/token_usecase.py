from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.token_repository import TokenRepository
from app.schemas.token import TokenCreate, TokenResponse


class TokenUsecase:
    """
    Use case layer for token operations. Handles business logic for creating
    and managing tokens.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.token_repository = TokenRepository(db)

    async def create_token(self, token: TokenCreate) -> TokenResponse:
        """
        Create a new token.
        Args:
            token: TokenCreate schema with token details.
        Returns:
            TokenResponse: The created token response object.
        """
        return await self.token_repository.create(token)
