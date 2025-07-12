from app.core.config import ConfigurationService
from app.repositories.historical_balance_repository import (
    HistoricalBalanceRepository,
)
from app.schemas.historical_balance import (
    HistoricalBalanceCreate,
    HistoricalBalanceResponse,
)
from app.utils.logging import Audit


class HistoricalBalanceUsecase:
    """
    Use case layer for historical balance operations with explicit dependency injection.
    Handles business logic for creating and managing historical balance records.
    """

    def __init__(
        self,
        historical_balance_repo: HistoricalBalanceRepository,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        self.__historical_balance_repo = historical_balance_repo
        self.__config_service = config_service
        self.__audit = audit

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
        self.__audit.info(
            "historical_balance_usecase_create_started",
            wallet_address=hb.wallet_address if hasattr(hb, "wallet_address") else None,
        )

        try:
            result = await self.__historical_balance_repo.create(hb)

            self.__audit.info(
                "historical_balance_usecase_create_success",
                historical_balance_id=str(result.id) if hasattr(result, "id") else None,
            )

            return result
        except Exception as e:
            self.__audit.error(
                "historical_balance_usecase_create_failed",
                error=str(e),
            )
            raise
