from sqlalchemy.ext.asyncio import AsyncSession

from app.models.historical_balance import HistoricalBalance
from app.schemas.historical_balance import HistoricalBalanceCreate


class HistoricalBalanceStore:
    @staticmethod
    async def create(
        db: AsyncSession, data: HistoricalBalanceCreate
    ) -> HistoricalBalance:
        hist_balance = HistoricalBalance(
            wallet_id=data.wallet_id,
            token_id=data.token_id,
            balance=data.balance,
            balance_usd=data.balance_usd,
            timestamp=data.timestamp,
        )
        db.add(hist_balance)
        await db.commit()
        await db.refresh(hist_balance)
        return hist_balance
