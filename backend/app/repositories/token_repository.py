from app.core.database import CoreDatabase
from app.domain.interfaces.repositories import TokenRepositoryInterface
from app.domain.schemas.token import TokenCreate
from app.models.token import Token
from app.utils.logging import Audit


class TokenRepository(TokenRepositoryInterface):
    """Repository for :class:`~app.models.token.Token`."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def create(self, data: TokenCreate) -> Token:
        """Create a new token record."""
        self.__audit.info(
            "token_repository_create_started",
            address=data.address,
            symbol=data.symbol,
            name=data.name,
        )

        try:
            async with self.__database.get_session() as session:
                token = Token(
                    address=data.address,
                    symbol=data.symbol,
                    name=data.name,
                    decimals=data.decimals,
                )
                session.add(token)
                await session.commit()
                await session.refresh(token)

                self.__audit.info(
                    "token_repository_create_success",
                    address=data.address,
                    symbol=data.symbol,
                    token_id=str(token.id),
                )
                return token
        except Exception as e:
            self.__audit.error(
                "token_repository_create_failed",
                address=data.address,
                symbol=data.symbol,
                error=str(e),
            )
            raise
