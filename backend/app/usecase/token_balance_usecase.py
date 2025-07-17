from app.core.config import ConfigurationService
from app.domain.schemas.token_balance import (
    TokenBalanceCreate,
    TokenBalanceResponse,
)
from app.repositories.token_balance_repository import TokenBalanceRepository
from app.utils.logging import Audit


class TokenBalanceUsecase:
    """
    Use case layer for token balance operations with explicit dependency injection.
    Handles business logic for creating and managing token balance records.
    """

    def __init__(
        self,
        token_balance_repo: TokenBalanceRepository,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        self.__token_balance_repo = token_balance_repo
        self.__config_service = config_service
        self.__audit = audit

    async def create_token_balance(
        self, tb: TokenBalanceCreate
    ) -> TokenBalanceResponse:
        """
        Create a new token balance record.
        Args:
            tb: TokenBalanceCreate schema with balance details.
        Returns:
            TokenBalanceResponse: The created token balance response object.
        """
        self.__audit.info(
            "token_balance_usecase_create_started",
            wallet_address=tb.wallet_address if hasattr(tb, "wallet_address") else None,
        )

        try:
            result = await self.__token_balance_repo.create(tb)

            self.__audit.info(
                "token_balance_usecase_create_success",
                token_balance_id=str(result.id) if hasattr(result, "id") else None,
            )

            return result
        except Exception as e:
            self.__audit.error(
                "token_balance_usecase_create_failed",
                error=str(e),
            )
            raise
