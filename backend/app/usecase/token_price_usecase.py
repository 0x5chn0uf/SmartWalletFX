from app.core.config import ConfigurationService
from app.domain.schemas.token_price import TokenPriceCreate, TokenPriceResponse
from app.repositories.token_price_repository import TokenPriceRepository
from app.utils.logging import Audit


class TokenPriceUsecase:
    """
    Use case layer for token price operations with explicit dependency injection.
    Handles business logic for creating and managing token price records.
    """

    def __init__(
        self,
        token_price_repo: TokenPriceRepository,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        self.__token_price_repo = token_price_repo
        self.__config_service = config_service
        self.__audit = audit

    async def create_token_price(self, tp: TokenPriceCreate) -> TokenPriceResponse:
        """
        Create a new token price record.
        Args:
            tp: TokenPriceCreate schema with price details.
        Returns:
            TokenPriceResponse: The created token price response object.
        """
        self.__audit.info(
            "token_price_usecase_create_started",
            token_symbol=tp.symbol if hasattr(tp, "symbol") else None,
        )

        try:
            result = await self.__token_price_repo.create(tp)

            self.__audit.info(
                "token_price_usecase_create_success",
                token_price_id=str(result.id) if hasattr(result, "id") else None,
            )

            return result
        except Exception as e:
            self.__audit.error(
                "token_price_usecase_create_failed",
                error=str(e),
            )
            raise
