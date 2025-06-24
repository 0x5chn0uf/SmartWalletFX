from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.historical_balance_repository import (
    HistoricalBalanceRepository,
)
from app.schemas.historical_balance import (
    HistoricalBalanceCreate,
    HistoricalBalanceResponse,
)


class HistoricalBalanceUsecase:
    """
    Use case layer for historical balance operations. Handles business logic
    for creating and managing historical balance records.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.historical_balance_repository = HistoricalBalanceRepository(db)

    async def create_historical_balance(
        self, hb: HistoricalBalanceCreate
    ) -> HistoricalBalanceResponse:
        """
        Create a new historical balance record.
        Args:
            hb: HistoricalBalanceCreate schema with balance details.
        Returns:
            HistoricalBalanceResponse: The created historical balance response object.
        """
        return await self.historical_balance_repository.create(hb)
