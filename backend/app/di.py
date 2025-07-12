"""Dependency Injection Container for managing singleton instances."""

from sqlalchemy.orm import Session

from app.core.config import ConfigurationService
from app.core.database import DatabaseService, SyncSessionLocal
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from app.repositories.historical_balance_repository import (
    HistoricalBalanceRepository,
)
from app.repositories.oauth_account_repository import OAuthAccountRepository
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.portfolio_snapshot_repository import (
    PortfolioSnapshotRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.token_balance_repository import TokenBalanceRepository
from app.repositories.token_price_repository import TokenPriceRepository
from app.repositories.token_repository import TokenRepository

# Repository imports
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository

# Usecase imports
from app.usecase.email_verification_usecase import EmailVerificationUsecase
from app.usecase.historical_balance_usecase import HistoricalBalanceUsecase
from app.usecase.oauth_usecase import OAuthUsecase
from app.usecase.portfolio_snapshot_usecase import PortfolioSnapshotUsecase
from app.usecase.token_balance_usecase import TokenBalanceUsecase
from app.usecase.token_price_usecase import TokenPriceUsecase
from app.usecase.token_usecase import TokenUsecase
from app.usecase.wallet_usecase import WalletUsecase
from app.utils.logging import Audit


class DIContainer:
    """
    Dependency Injection Container managing singleton instances of all
    services, repositories, usecases, and endpoints.
    """

    def __init__(self):
        self._services = {}
        self._repositories = {}
        self._usecases = {}
        self._endpoints = {}
        self._initialize_services()

    def _initialize_services(self):
        """Initialize and register core services as singletons."""
        # Create and register core services
        config_service = ConfigurationService()
        self.register_service("config", config_service)

        database_service = DatabaseService(config_service)
        self.register_service("database", database_service)

        # Use existing Audit service from app.utils.logging
        audit_service = Audit()
        self.register_service("audit", audit_service)

        # TODO: Add other services as we refactor them
        # email_service = EmailService(config_service)
        # self.register_service("email", email_service)

        # jwt_utils = JWTUtils(config_service)
        # self.register_service("jwt_utils", jwt_utils)

        # Create and register singleton repositories (Phase 2)
        self._initialize_repositories()

        # Create and register singleton usecases (Phase 3)
        self._initialize_usecases()

        # Create and register singleton endpoints (Phase 4)
        self._initialize_endpoints()

    def _initialize_repositories(self):
        """Initialize and register repository singletons."""
        database_service = self.get_service("database")
        audit_service = self.get_service("audit")

        # Register repositories with explicit dependency injection
        user_repository = UserRepository(database_service, audit_service)
        self.register_repository("user", user_repository)

        email_verification_repository = EmailVerificationRepository(
            database_service, audit_service
        )
        self.register_repository("email_verification", email_verification_repository)

        oauth_account_repository = OAuthAccountRepository(
            database_service, audit_service
        )
        self.register_repository("oauth_account", oauth_account_repository)

        password_reset_repository = PasswordResetRepository(
            database_service, audit_service
        )
        self.register_repository("password_reset", password_reset_repository)

        refresh_token_repository = RefreshTokenRepository(
            database_service, audit_service
        )
        self.register_repository("refresh_token", refresh_token_repository)

        wallet_repository = WalletRepository(database_service, audit_service)
        self.register_repository("wallet", wallet_repository)

        portfolio_snapshot_repository = PortfolioSnapshotRepository(
            database_service, audit_service
        )
        self.register_repository("portfolio_snapshot", portfolio_snapshot_repository)

        historical_balance_repository = HistoricalBalanceRepository(
            database_service, audit_service
        )
        self.register_repository("historical_balance", historical_balance_repository)

        token_repository = TokenRepository(database_service, audit_service)
        self.register_repository("token", token_repository)

        token_price_repository = TokenPriceRepository(database_service, audit_service)
        self.register_repository("token_price", token_price_repository)

        token_balance_repository = TokenBalanceRepository(
            database_service, audit_service
        )
        self.register_repository("token_balance", token_balance_repository)

    def _initialize_usecases(self):
        """Initialize and register usecase singletons."""
        # Get required services
        config_service = self.get_service("config")
        audit_service = self.get_service("audit")

        # Get repositories
        user_repo = self.get_repository("user")
        email_verification_repo = self.get_repository("email_verification")
        oauth_account_repo = self.get_repository("oauth_account")
        refresh_token_repo = self.get_repository("refresh_token")
        wallet_repo = self.get_repository("wallet")
        portfolio_snapshot_repo = self.get_repository("portfolio_snapshot")
        historical_balance_repo = self.get_repository("historical_balance")
        token_repo = self.get_repository("token")
        token_price_repo = self.get_repository("token_price")
        token_balance_repo = self.get_repository("token_balance")

        # TODO: Add these services when they are refactored
        # email_service = self.get_service("email")
        # jwt_utils = self.get_service("jwt_utils")

        # Create and register usecases
        # Note: EmailVerificationUsecase needs email_service and jwt_utils
        # For now, we'll register it with placeholders
        email_verification_uc = EmailVerificationUsecase(
            email_verification_repo,
            user_repo,
            refresh_token_repo,
            None,  # email_service - TODO: add when refactored
            None,  # jwt_utils - TODO: add when refactored
            config_service,
            audit_service,
        )
        self.register_usecase("email_verification", email_verification_uc)

        wallet_uc = WalletUsecase(
            wallet_repo,
            portfolio_snapshot_repo,
            config_service,
            audit_service,
        )
        self.register_usecase("wallet", wallet_uc)

        oauth_uc = OAuthUsecase(
            oauth_account_repo,
            user_repo,
            refresh_token_repo,
            config_service,
            audit_service,
        )
        self.register_usecase("oauth", oauth_uc)

        token_price_uc = TokenPriceUsecase(
            token_price_repo,
            config_service,
            audit_service,
        )
        self.register_usecase("token_price", token_price_uc)

        token_uc = TokenUsecase(
            token_repo,
            config_service,
            audit_service,
        )
        self.register_usecase("token", token_uc)

        historical_balance_uc = HistoricalBalanceUsecase(
            historical_balance_repo,
            config_service,
            audit_service,
        )
        self.register_usecase("historical_balance", historical_balance_uc)

        token_balance_uc = TokenBalanceUsecase(
            token_balance_repo,
            config_service,
            audit_service,
        )
        self.register_usecase("token_balance", token_balance_uc)

        portfolio_snapshot_uc = PortfolioSnapshotUsecase(
            portfolio_snapshot_repo,
            audit_service,
        )
        self.register_usecase("portfolio_snapshot", portfolio_snapshot_uc)

    def _initialize_endpoints(self):
        """Initialize and register endpoint singletons."""
        # Import endpoint classes
        from app.api.endpoints.admin import Admin
        from app.api.endpoints.admin_db import AdminDB
        from app.api.endpoints.email_verification import EmailVerification
        from app.api.endpoints.health import Health
        from app.api.endpoints.jwks import JWKS
        from app.api.endpoints.oauth import OAuth
        from app.api.endpoints.users import Users
        from app.api.endpoints.wallets import Wallets

        # Get required usecases
        email_verification_uc = self.get_usecase("email_verification")
        oauth_uc = self.get_usecase("oauth")
        wallet_uc = self.get_usecase("wallet")
        token_uc = self.get_usecase("token")
        historical_balance_uc = self.get_usecase("historical_balance")
        token_price_uc = self.get_usecase("token_price")
        token_balance_uc = self.get_usecase("token_balance")
        portfolio_snapshot_uc = self.get_usecase("portfolio_snapshot")

        # Get required repositories for endpoints that need them directly
        user_repo = self.get_repository("user")

        # TODO: Add these services when they are refactored
        # email_service = self.get_service("email")
        # auth_service = self.get_service("auth")

        # Create and register endpoint singletons
        email_verification_endpoint = EmailVerification(email_verification_uc)
        self.register_endpoint("email_verification", email_verification_endpoint)

        oauth_endpoint = OAuth(oauth_uc)
        self.register_endpoint("oauth", oauth_endpoint)

        wallets_endpoint = Wallets(
            wallet_uc,
            token_uc,
            historical_balance_uc,
            token_price_uc,
            token_balance_uc,
            portfolio_snapshot_uc,
        )
        self.register_endpoint("wallets", wallets_endpoint)

        # Simple endpoints that don't need dependencies
        health_endpoint = Health()
        self.register_endpoint("health", health_endpoint)

        jwks_endpoint = JWKS()
        self.register_endpoint("jwks", jwks_endpoint)

        admin_db_endpoint = AdminDB()
        self.register_endpoint("admin_db", admin_db_endpoint)

        # Endpoints that need repository dependencies
        users_endpoint = Users(user_repo)
        self.register_endpoint("users", users_endpoint)

        admin_endpoint = Admin(user_repo)
        self.register_endpoint("admin", admin_endpoint)

        # TODO: Add password_reset_endpoint when EmailService is refactored
        # password_reset_repo = self.get_repository("password_reset")
        # password_reset_endpoint = PasswordReset(
        #     password_reset_repo,
        #     user_repo,
        #     email_service,
        # )
        # self.register_endpoint("password_reset", password_reset_endpoint)

        # TODO: Add auth_endpoint when AuthService is refactored
        # auth_endpoint = Auth(auth_service)
        # self.register_endpoint("auth", auth_endpoint)

    def register_service(self, name: str, service):
        """Register a service singleton."""
        self._services[name] = service

    def register_repository(self, name: str, repository):
        """Register a repository singleton."""
        self._repositories[name] = repository

    def register_usecase(self, name: str, usecase):
        """Register a usecase singleton."""
        self._usecases[name] = usecase

    def register_endpoint(self, name: str, endpoint):
        """Register an endpoint singleton."""
        self._endpoints[name] = endpoint

    def get_service(self, name: str):
        """Get a service singleton by name."""
        return self._services.get(name)

    def get_repository(self, name: str):
        """Get a repository singleton by name."""
        return self._repositories.get(name)

    def get_usecase(self, name: str):
        """Get a usecase singleton by name."""
        return self._usecases.get(name)

    def get_endpoint(self, name: str):
        """Get an endpoint singleton by name."""
        return self._endpoints.get(name)


# Keep existing simple DI helpers for backward compatibility during transition
def get_session_sync() -> Session:  # pragma: no cover
    """Return a new synchronous SQLAlchemy Session."""
    return SyncSessionLocal()
