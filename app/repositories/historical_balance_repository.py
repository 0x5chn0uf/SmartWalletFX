from app.core.database import CoreDatabase
from app.domain.interfaces.repositories import (
    HistoricalBalanceRepositoryInterface,
)
from app.domain.schemas.historical_balance import HistoricalBalanceCreate
from app.models.historical_balance import HistoricalBalance
from app.utils.logging import Audit


class HistoricalBalanceRepository(HistoricalBalanceRepositoryInterface):
    """Repository for :class:`~app.models.historical_balance.HistoricalBalance`."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def create(self, data: HistoricalBalanceCreate) -> HistoricalBalance:
        """Create a new historical balance record."""
        self.__audit.info(
            "historical_balance_repository_create_started",
            wallet_id=str(data.wallet_id),
            token_id=str(data.token_id),
            timestamp=data.timestamp,
        )

        try:
            async with self.__database.get_session() as session:
                hist_balance = HistoricalBalance(
                    wallet_id=data.wallet_id,
                    token_id=data.token_id,
                    balance=data.balance,
                    balance_usd=data.balance_usd,
                    timestamp=data.timestamp,
                )
                session.add(hist_balance)
                await session.commit()
                await session.refresh(hist_balance)

                self.__audit.info(
                    "historical_balance_repository_create_success",
                    wallet_id=str(data.wallet_id),
                    token_id=str(data.token_id),
                    balance_id=str(hist_balance.id),
                )
                return hist_balance
        except Exception as e:
            self.__audit.error(
                "historical_balance_repository_create_failed",
                wallet_id=str(data.wallet_id),
                token_id=str(data.token_id),
                error=str(e),
            )
            raise
