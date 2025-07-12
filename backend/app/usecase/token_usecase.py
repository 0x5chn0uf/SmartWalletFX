from app.core.config import ConfigurationService
from app.repositories.token_repository import TokenRepository
from app.schemas.token import TokenCreate, TokenResponse
from app.utils.logging import Audit


class TokenUsecase:
    """
    Use case layer for token operations with explicit dependency injection.
    Handles business logic for creating and managing token records.
    """

    def __init__(
        self,
        token_repo: TokenRepository,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        self.__token_repo = token_repo
        self.__config_service = config_service
        self.__audit = audit

    async def create_token(self, token: TokenCreate) -> TokenResponse:
        """
        Create a new token record.
        Args:
            token: TokenCreate schema with token details.
        Returns:
            TokenResponse: The created token response object.
        """
        self.__audit.info(
            "token_usecase_create_started",
            token_symbol=token.symbol if hasattr(token, 'symbol') else None,
        )
        
        try:
            result = await self.__token_repo.create(token)
            
            self.__audit.info(
                "token_usecase_create_success",
                token_id=str(result.id) if hasattr(result, 'id') else None,
            )
            
            return result
        except Exception as e:
            self.__audit.error(
                "token_usecase_create_failed",
                error=str(e),
            )
            raise
