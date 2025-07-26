"""Dependency Injection Container for managing singleton instances."""

# Import endpoint classes
from app.api.endpoints.admin import Admin
from app.api.endpoints.auth import Auth
from app.api.endpoints.defi import DeFi
from app.api.endpoints.email_verification import EmailVerification
from app.api.endpoints.health import Health
from app.api.endpoints.jwks import JWKS
from app.api.endpoints.oauth import OAuth
from app.api.endpoints.password_reset import PasswordReset
from app.api.endpoints.users import Users
from app.api.endpoints.wallets import Wallets
from app.core.celery import CoreCelery
from app.core.config import Configuration
from app.core.database import CoreDatabase
from app.core.error_handling import CoreErrorHandling
from app.core.logging import CoreLogging
from app.core.middleware import Middleware
from app.domain.interfaces.repositories import (
    EmailVerificationRepositoryInterface,
    HistoricalBalanceRepositoryInterface,
    OAuthAccountRepositoryInterface,
    PasswordResetRepositoryInterface,
    PortfolioSnapshotRepositoryInterface,
    RefreshTokenRepositoryInterface,
    TokenBalanceRepositoryInterface,
    TokenPriceRepositoryInterface,
    TokenRepositoryInterface,
    UserRepositoryInterface,
    WalletRepositoryInterface,
)
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
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository

# Repository imports
from app.services.email_service import EmailService
from app.services.file_upload_service import FileUploadService
from app.services.oauth_service import OAuthService
from app.usecase.auth_usecase import AuthUsecase

# Usecase imports
from app.usecase.email_verification_usecase import EmailVerificationUsecase
from app.usecase.historical_balance_usecase import HistoricalBalanceUsecase
from app.usecase.oauth_usecase import OAuthUsecase
from app.usecase.portfolio_snapshot_usecase import PortfolioSnapshotUsecase
from app.usecase.token_balance_usecase import TokenBalanceUsecase
from app.usecase.token_price_usecase import TokenPriceUsecase
from app.usecase.token_usecase import TokenUsecase
from app.usecase.user_profile_usecase import UserProfileUsecase
from app.usecase.wallet_usecase import WalletUsecase
from app.utils.encryption import EncryptionUtils
from app.utils.jwks_cache import JWKSCacheUtils
from app.utils.jwt import JWTUtils
from app.utils.jwt_keys import JWTKeyUtils
from app.utils.logging import Audit
from app.utils.rate_limiter import RateLimiterUtils
from app.utils.security import PasswordHasher


class DIContainer:
    """
    Dependency Injection Container managing singleton instances of all
    services, repositories, usecases, and endpoints.
    """

    def __init__(self):
        """Initialize the container, register services, and set up dependencies."""
        self._core = {}
        self._services = {}
        self._repositories = {}
        self._usecases = {}
        self._endpoints = {}
        self._utilities = {}
        self._initialize_core()
        self._initialize_utilities()
        self._initialize_repositories()
        self._initialize_services()
        self._initialize_usecases()
        self._initialize_endpoints()

    def _initialize_core(self):
        """Initialize and register core services as singletons."""
        config = Configuration()
        self.register_core("config", config)

        audit = Audit()
        self.register_core("audit", audit)

        database = CoreDatabase(config, audit)
        self.register_core("database", database)

        logging = CoreLogging(config)
        self.register_core("logging", logging)

        celery = CoreCelery(config)
        self.register_core("celery", celery)

        error_handling = CoreErrorHandling(audit)
        self.register_core("error_handling", error_handling)

        middleware = Middleware(audit)
        self.register_core("middleware", middleware)

    def _initialize_services(self):
        """Initialize and register core services as singletons."""
        config = self.get_core("config")
        audit = self.get_core("audit")
        user_repo = self.get_repository("user")
        oauth_account_repo = self.get_repository("oauth_account")
        refresh_token_repo = self.get_repository("refresh_token")
        jwt_utils = self.get_utility("jwt_utils")

        # Initialize OAuth service here since it needs jwt_utils
        oauth_service = OAuthService(
            user_repo,
            oauth_account_repo,
            refresh_token_repo,
            jwt_utils,
            config,
            audit,
        )
        self.register_service("oauth", oauth_service)

        email_service = EmailService(config, audit)
        self.register_service("email", email_service)

        file_upload_service = FileUploadService(audit)
        self.register_service("file_upload", file_upload_service)

    def _initialize_utilities(self):
        """Initialize and register utility classes."""
        config = self.get_core("config")
        audit = self.get_core("audit")

        jwt_utils = JWTUtils(config, audit)
        self.register_utility("jwt_utils", jwt_utils)

        encryption_utils = EncryptionUtils(config)
        self.register_utility("encryption_utils", encryption_utils)

        jwks_cache_utils = JWKSCacheUtils(config)
        self.register_utility("jwks_cache_utils", jwks_cache_utils)

        jwt_key_utils = JWTKeyUtils(config)
        self.register_utility("jwt_key_utils", jwt_key_utils)

        rate_limiter_utils = RateLimiterUtils(config)
        self.register_utility("rate_limiter_utils", rate_limiter_utils)

        password_hasher = PasswordHasher(config)
        self.register_utility("password_hasher", password_hasher)

    def _initialize_repositories(self):
        """Initialize and register repository singletons."""
        database = self.get_core("database")
        audit = self.get_core("audit")

        # Register repositories with explicit dependency injection
        user_repository = UserRepository(database, audit)
        self.register_repository("user", user_repository)

        email_verification_repository = EmailVerificationRepository(database, audit)
        self.register_repository(
            "email_verification",
            email_verification_repository,
        )

        oauth_account_repository = OAuthAccountRepository(database, audit)
        self.register_repository(
            "oauth_account",
            oauth_account_repository,
        )

        password_reset_repository = PasswordResetRepository(database, audit)
        self.register_repository(
            "password_reset",
            password_reset_repository,
        )

        refresh_token_repository = RefreshTokenRepository(database, audit)
        self.register_repository(
            "refresh_token",
            refresh_token_repository,
        )

        wallet_repository = WalletRepository(database, audit)
        self.register_repository("wallet", wallet_repository)

        portfolio_snapshot_repository = PortfolioSnapshotRepository(database, audit)
        self.register_repository(
            "portfolio_snapshot",
            portfolio_snapshot_repository,
        )

        historical_balance_repository = HistoricalBalanceRepository(database, audit)
        self.register_repository(
            "historical_balance",
            historical_balance_repository,
        )

        token_repository = TokenRepository(database, audit)
        self.register_repository("token", token_repository)

        token_price_repository = TokenPriceRepository(database, audit)
        self.register_repository(
            "token_price",
            token_price_repository,
        )

        token_balance_repository = TokenBalanceRepository(database, audit)
        self.register_repository(
            "token_balance",
            token_balance_repository,
        )

    def _initialize_usecases(self):
        """Initialize and register usecase singletons."""
        # Get required services
        config = self.get_core("config")
        audit = self.get_core("audit")

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

        # Get the newly added services
        email_service = self.get_service("email")
        jwt_utils = self.get_utility("jwt_utils")

        # Create and register usecases
        auth_usecase = AuthUsecase(
            user_repo,
            email_verification_repo,
            refresh_token_repo,
            email_service,
            jwt_utils,
            config,
            audit,
        )
        self.register_usecase("auth", auth_usecase)

        email_verification_uc = EmailVerificationUsecase(
            email_verification_repo,
            user_repo,
            refresh_token_repo,
            email_service,
            jwt_utils,
            config,
            audit,
        )
        self.register_usecase("email_verification", email_verification_uc)

        wallet_uc = WalletUsecase(
            wallet_repo,
            user_repo,
            portfolio_snapshot_repo,
            config,
            audit,
        )
        self.register_usecase("wallet", wallet_uc)

        # Get OAuthService
        oauth_service = self.get_service("oauth")

        oauth_uc = OAuthUsecase(
            oauth_account_repo,
            user_repo,
            refresh_token_repo,
            oauth_service,
            config,
            audit,
        )
        self.register_usecase("oauth", oauth_uc)

        token_price_uc = TokenPriceUsecase(
            token_price_repo,
            config,
            audit,
        )
        self.register_usecase("token_price", token_price_uc)

        token_uc = TokenUsecase(
            token_repo,
            config,
            audit,
        )
        self.register_usecase("token", token_uc)

        historical_balance_uc = HistoricalBalanceUsecase(
            historical_balance_repo,
            config,
            audit,
        )
        self.register_usecase("historical_balance", historical_balance_uc)

        token_balance_uc = TokenBalanceUsecase(
            token_balance_repo,
            config,
            audit,
        )
        self.register_usecase("token_balance", token_balance_uc)

        portfolio_snapshot_uc = PortfolioSnapshotUsecase(
            portfolio_snapshot_repo,
            wallet_repo,
            audit,
        )
        self.register_usecase("portfolio_snapshot", portfolio_snapshot_uc)

        # User profile usecase
        user_profile_uc = UserProfileUsecase(user_repo, audit)
        self.register_usecase("user_profile", user_profile_uc)

    def _initialize_endpoints(self):
        """Initialize and register endpoint singletons."""
        # Get core components
        self.get_core("audit")

        # Get usecases
        auth_usecase = self.get_usecase("auth")
        self.get_service("oauth")
        email_service = self.get_service("email")

        # Get usecases
        email_verification_uc = self.get_usecase("email_verification")
        oauth_uc = self.get_usecase("oauth")
        wallet_uc = self.get_usecase("wallet")
        token_uc = self.get_usecase("token")
        token_balance_uc = self.get_usecase("token_balance")
        token_price_uc = self.get_usecase("token_price")
        historical_balance_uc = self.get_usecase("historical_balance")
        portfolio_snapshot_uc = self.get_usecase("portfolio_snapshot")

        # Get repositories
        user_repo = self.get_repository("user")
        password_reset_repo = self.get_repository("password_reset")

        # Create and register endpoints
        admin_endpoint = Admin(user_repo)
        self.register_endpoint("admin", admin_endpoint)

        rate_limiter_utils = self.get_utility("rate_limiter_utils")
        auth_endpoint = Auth(auth_usecase, rate_limiter_utils)
        self.register_endpoint("auth", auth_endpoint)

        email_verification_endpoint = EmailVerification(email_verification_uc)
        self.register_endpoint("email_verification", email_verification_endpoint)

        health_endpoint = Health()
        self.register_endpoint("health", health_endpoint)

        jwks_endpoint = JWKS()
        self.register_endpoint("jwks", jwks_endpoint)

        oauth_endpoint = OAuth(oauth_uc)
        self.register_endpoint("oauth", oauth_endpoint)

        password_hasher = self.get_utility("password_hasher")
        config = self.get_core("config")
        password_reset_endpoint = PasswordReset(
            password_reset_repo,
            user_repo,
            email_service,
            rate_limiter_utils,
            password_hasher,
            config,
        )
        self.register_endpoint("password_reset", password_reset_endpoint)

        user_profile_uc = self.get_usecase("user_profile")
        file_upload_service = self.get_service("file_upload")
        users_endpoint = Users(user_repo, user_profile_uc, file_upload_service)
        self.register_endpoint("users", users_endpoint)

        wallets_endpoint = Wallets(
            wallet_uc,
            token_uc,
            historical_balance_uc,
            token_price_uc,
            token_balance_uc,
            portfolio_snapshot_uc,
        )
        self.register_endpoint("wallets", wallets_endpoint)

        defi_endpoint = DeFi(wallet_uc)
        self.register_endpoint("defi", defi_endpoint)

    def register_core(self, name: str, core):
        """Register a Core instance."""
        self._core[name] = core

    def register_service(self, name: str, service):
        """Register a service instance."""
        self._services[name] = service

    def register_repository(self, name: str, repository):
        """Register a repository instance."""
        self._repositories[name] = repository

    def register_usecase(self, name: str, usecase):
        """Register a usecase instance."""
        self._usecases[name] = usecase

    def register_utility(self, name: str, utility):
        """Register an endpoint instance."""
        self._utilities[name] = utility

    def register_endpoint(self, name: str, endpoint):
        """Register an endpoint instance."""
        self._endpoints[name] = endpoint

    def get_core(self, name: str):
        """Get a core instance by name."""
        core = self._core.get(name)
        if not core:
            raise ValueError(f"Core '{name}' not found.")
        return core

    def get_service(self, name: str):
        """Get a service instance by name."""
        service = self._services.get(name)
        if not service:
            raise ValueError(f"Service '{name}' not found.")
        return service

    def get_repository(self, name: str):
        """Get a repository instance by name."""
        repository = self._repositories.get(name)
        if not repository:
            raise ValueError(f"Repository '{name}' not found.")
        return repository

    def get_usecase(self, name: str):
        """Get a usecase instance by name."""
        usecase = self._usecases.get(name)
        if not usecase:
            raise ValueError(f"Usecase '{name}' not found.")
        return usecase

    def get_utility(self, name: str):
        """Get a utility instance by name."""
        utility = self._utilities.get(name)
        if not utility:
            raise ValueError(f"Utility '{name}' not found.")
        return utility

    def get_endpoint(self, name: str):
        """Get an endpoint instance by name."""
        endpoint = self._endpoints.get(name)
        if not endpoint:
            raise ValueError(f"Endpoint '{name}' not found.")
        return endpoint
