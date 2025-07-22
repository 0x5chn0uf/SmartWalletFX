from app.core.database import CoreDatabase
from app.domain.schemas.token_price import TokenPriceCreate
from app.models.token_price import TokenPrice
from app.utils.logging import Audit


class TokenPriceRepository:
    """Repository for :class:`~app.models.token_price.TokenPrice`."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def create(self, data: TokenPriceCreate) -> TokenPrice:
        """Create a new token price record."""
        self.__audit.info(
            "token_price_repository_create_started",
            token_id=str(data.token_id),
            price_usd=data.price_usd,
        )

        try:
            async with self.__database.get_session() as session:
                price = TokenPrice(
                    token_id=data.token_id,
                    price_usd=data.price_usd,
                )
                session.add(price)
                await session.commit()
                await session.refresh(price)

                self.__audit.info(
                    "token_price_repository_create_success",
                    token_id=str(data.token_id),
                    price_id=str(price.id),
                )
                return price
        except Exception as e:
            self.__audit.error(
                "token_price_repository_create_failed",
                token_id=str(data.token_id),
                error=str(e),
            )
            raise
