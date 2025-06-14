from sqlalchemy.ext.asyncio import AsyncSession

from app.models.historical_balance import HistoricalBalance
from app.schemas.historical_balance import HistoricalBalanceCreate


class HistoricalBalanceStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: HistoricalBalanceCreate) -> HistoricalBalance:
        hist_balance = HistoricalBalance(
            wallet_id=data.wallet_id,
            token_id=data.token_id,
            balance=data.balance,
            balance_usd=data.balance_usd,
            timestamp=data.timestamp,
        )
        self.db.add(hist_balance)
        await self.db.commit()
        await self.db.refresh(hist_balance)
        return hist_balance
