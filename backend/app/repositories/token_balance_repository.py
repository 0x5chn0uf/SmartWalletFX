from app.core.database import CoreDatabase
from app.domain.schemas.token_balance import TokenBalanceCreate
from app.models.token_balance import TokenBalance
from app.utils.logging import Audit


class TokenBalanceRepository:
    """Repository for :class:`~app.models.token_balance.TokenBalance`."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def create(self, data: TokenBalanceCreate) -> TokenBalance:
        """Create a new token balance record."""
        self.__audit.info(
            "token_balance_repository_create_started",
            token_id=str(data.token_id),
            wallet_id=str(data.wallet_id),
            balance=data.balance,
        )

        try:
            async with self.__database.get_session() as session:
                balance = TokenBalance(
                    token_id=data.token_id,
                    wallet_id=data.wallet_id,
                    balance=data.balance,
                    balance_usd=data.balance_usd,
                )
                session.add(balance)
                await session.commit()
                await session.refresh(balance)

                self.__audit.info(
                    "token_balance_repository_create_success",
                    token_id=str(data.token_id),
                    wallet_id=str(data.wallet_id),
                    balance_id=str(balance.id),
                )
                return balance
        except Exception as e:
            self.__audit.error(
                "token_balance_repository_create_failed",
                token_id=str(data.token_id),
                wallet_id=str(data.wallet_id),
                error=str(e),
            )
            raise
