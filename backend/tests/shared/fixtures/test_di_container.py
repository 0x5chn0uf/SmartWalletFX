"""
Test-specific DI Container for isolated testing.

This module provides a test-optimized DI container that:
1. Uses test-specific configurations
2. Provides proper service mocking
3. Isolates test dependencies from production code
4. Supports both unit and integration testing scenarios
"""

from contextlib import asynccontextmanager
from typing import Any, Optional
from unittest.mock import AsyncMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Configuration
from app.core.database import CoreDatabase
from app.di import DIContainer

# Import repository interfaces (with error handling)
try:
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
except ImportError:
    # Fallback to ABC for basic interface mocking
    from abc import ABC

    EmailVerificationRepositoryInterface = ABC
    HistoricalBalanceRepositoryInterface = ABC
    OAuthAccountRepositoryInterface = ABC
    PasswordResetRepositoryInterface = ABC
    PortfolioSnapshotRepositoryInterface = ABC
    RefreshTokenRepositoryInterface = ABC
    TokenBalanceRepositoryInterface = ABC
    TokenPriceRepositoryInterface = ABC
    TokenRepositoryInterface = ABC
    UserRepositoryInterface = ABC
    WalletRepositoryInterface = ABC


class TestDIContainer(DIContainer):
    """Test-specific DI container with enhanced mocking capabilities."""

    def __init__(
        self,
        test_config: Optional[Configuration] = None,
        test_session: Optional[AsyncSession] = None,
        test_database: Optional[CoreDatabase] = None,
    ):
        """Initialize test DI container with test-specific configuration.

        Args:
            test_config: Test configuration override
            test_session: Test database session for integration tests
            test_database: Test database instance for integration tests
        """
        # Initialize base container attributes (don't call super().__init__() to avoid production services)
        self._core = {}
        self._services = {}
        self._repositories = {}
        self._usecases = {}
        self._endpoints = {}
        self._utilities = {}

        self._test_config = test_config
        self._test_session = test_session
        self._test_database = test_database

        # Register test-specific services
        self._register_test_services()
        self._register_test_utilities()
        self._register_test_repositories()
        self._register_test_usecases()
        self._register_test_endpoints()

    def _register_test_services(self):
        """Register test-specific core services."""
        # Test configuration
        if self._test_config:
            self.register_core("config", self._test_config)
        else:
            # Create test configuration for unit tests
            from tests.shared.fixtures.test_config import (
                create_unit_test_config,
            )

            test_config = create_unit_test_config()
            self.register_core("config", test_config)

        # Mock audit service
        self._register_mock_audit()

        # Test database
        if self._test_session and self._test_database:
            # Integration test: use provided database instance with test session
            self._register_provided_database()
        elif self._test_session:
            # Integration test: use real database with test session
            self._register_integration_database()
        else:
            # Unit test: use mock database
            self._register_mock_database()

        # Mock logging service
        self._register_mock_logging()

        # Mock celery service
        self._register_mock_celery()

        # Mock error handling service
        self._register_mock_error_handling()

        # Mock middleware service
        self._register_mock_middleware()

        # Mock external services
        self._register_mock_external_services()

    def _register_mock_database(self):
        """Register mock database service for tests."""
        from app.core.database import CoreDatabase

        mock_database = Mock(spec=CoreDatabase)
        mock_database.get_session = AsyncMock()
        mock_database.init_db = AsyncMock()  # Add this for startup events
        mock_database.config = self.get_core("config")
        mock_database.async_engine = Mock()
        mock_database.sync_engine = Mock()
        self.register_core("database", mock_database)

    def _register_integration_database(self):
        """Register real database service for integration tests."""
        from app.utils.logging import Audit

        # Create a real CoreDatabase instance for integration tests
        config = self.get_core("config")
        audit = Audit()
        real_database = CoreDatabase(config, audit)

        # Override get_session to use the test session
        @asynccontextmanager
        async def get_test_session():
            """Provide the test database session."""
            yield self._test_session

        real_database.get_session = get_test_session
        self.register_core("database", real_database)

    def _register_provided_database(self):
        """Register provided database instance for integration tests."""

        # Use the provided database instance but override get_session to use test session
        @asynccontextmanager
        async def get_test_session():
            """Provide the test database session."""
            yield self._test_session

        self._test_database.get_session = get_test_session
        self.register_core("database", self._test_database)

    def _register_test_utilities(self):
        """Register test-specific utilities."""
        # Rate-limiter utils – real implementation for integration tests so
        # rate-limit related endpoints behave correctly (429 after N attempts).
        # Unit tests keep the lightweight mock to avoid unnecessary delays.

        from app.utils.rate_limiter import RateLimiterUtils

        if self._test_session:
            # Integration tests (real DB session provided) → use actual in-memory
            # rate-limiter so the business logic can trigger 429 responses that
            # the tests assert against.
            real_rate_limiter_utils = RateLimiterUtils(self.get_core("config"))
            self.register_utility("rate_limiter_utils", real_rate_limiter_utils)
        else:
            # Unit tests – preserve previous mock behaviour for speed.
            mock_rate_limiter = Mock(spec=RateLimiterUtils)
            mock_rate_limiter.login_rate_limiter = Mock()
            mock_rate_limiter.login_rate_limiter.allow = Mock(return_value=True)
            mock_rate_limiter.login_rate_limiter.reset = Mock()
            self.register_utility("rate_limiter_utils", mock_rate_limiter)

        # JWT utils - use real implementation for integration tests with session
        from app.utils.jwt import JWTUtils

        if self._test_session:
            # Integration tests: use real JWT utils
            config = self.get_core("config")
            audit = self.get_core("audit")
            real_jwt_utils = JWTUtils(config, audit)
            self.register_utility("jwt_utils", real_jwt_utils)
        else:
            # Unit tests: use mock JWT utils
            mock_jwt_utils = Mock(spec=JWTUtils)
            # Add JWT methods that usecases need
            mock_jwt_utils.create_access_token = Mock(return_value="mock_access_token")
            mock_jwt_utils.create_refresh_token = Mock(
                return_value="mock_refresh_token"
            )
            mock_jwt_utils.decode_token = Mock()
            mock_jwt_utils.verify_token = Mock(return_value=True)
            self.register_utility("jwt_utils", mock_jwt_utils)

        # Mock encryption utils
        from app.utils.encryption import EncryptionUtils

        mock_encryption_utils = Mock(spec=EncryptionUtils)
        self.register_utility("encryption_utils", mock_encryption_utils)

        # Mock JWKS cache utils
        from app.utils.jwks_cache import JWKSCacheUtils

        mock_jwks_cache = Mock(spec=JWKSCacheUtils)
        self.register_utility("jwks_cache_utils", mock_jwks_cache)

        # Mock JWT key utils
        from app.utils.jwt_keys import JWTKeyUtils

        mock_jwt_key_utils = Mock(spec=JWTKeyUtils)
        self.register_utility("jwt_key_utils", mock_jwt_key_utils)

        # Mock password hasher
        from app.utils.security import PasswordHasher

        mock_password_hasher = Mock(spec=PasswordHasher)
        self.register_utility("password_hasher", mock_password_hasher)

    def _register_mock_audit(self):
        """Register mock audit service for tests."""
        from app.utils.logging import Audit

        mock_audit = Mock(spec=Audit)
        self.register_core("audit", mock_audit)

    def _register_mock_logging(self):
        """Register mock logging service for tests."""
        from app.core.logging import CoreLogging

        mock_logging = Mock(spec=CoreLogging)
        mock_logging.get_logger = Mock(return_value=Mock())
        mock_logging.setup_logging = Mock()  # Add this for ApplicationFactory
        mock_logging.info = Mock()
        mock_logging.error = Mock()
        self.register_core("logging", mock_logging)

    def _register_mock_celery(self):
        """Register mock celery service for tests."""
        from app.core.celery import CoreCelery

        mock_celery = Mock(spec=CoreCelery)
        self.register_core("celery", mock_celery)

    def _register_mock_error_handling(self):
        """Register mock error handling service for tests."""
        from app.core.error_handling import CoreErrorHandling

        mock_error_handling = Mock(spec=CoreErrorHandling)
        self.register_core("error_handling", mock_error_handling)

    def _register_mock_middleware(self):
        """Register mock middleware service for tests."""
        from app.core.middleware import Middleware

        mock_middleware = Mock(spec=Middleware)
        self.register_core("middleware", mock_middleware)

    def _register_mock_external_services(self):
        """Register mock external services."""
        # Email service
        from app.services.email_service import EmailService

        mock_email = Mock(spec=EmailService)
        mock_email.send_verification_email = AsyncMock(return_value=True)
        mock_email.send_password_reset_email = AsyncMock(return_value=True)
        self.register_service("email", mock_email)

        # File upload service
        from app.services.file_upload_service import FileUploadService

        mock_file_upload = Mock(spec=FileUploadService)
        mock_file_upload.upload_profile_picture = AsyncMock(
            return_value="https://example.com/pic.jpg"
        )
        mock_file_upload.delete_profile_picture = AsyncMock(return_value=True)
        self.register_service("file_upload", mock_file_upload)

        # OAuth service
        from app.services.oauth_service import OAuthService

        mock_oauth = Mock(spec=OAuthService)
        mock_oauth.exchange_code = AsyncMock(
            return_value={"access_token": "test-token"}
        )
        self.register_service("oauth", mock_oauth)

    def _register_test_repositories(self):
        """Register repositories for testing (real for integration, mocks for unit)."""
        if self._test_session:
            # Integration tests: use real repositories with test database session
            self._register_real_repositories()
        else:
            # Unit tests: use mock repositories
            self._register_mock_repositories()

    def _register_real_repositories(self):
        """Register real repositories for integration testing."""
        try:
            # Import real repository implementations
            from app.repositories.email_verification_repository import (
                EmailVerificationRepository,
            )
            from app.repositories.refresh_token_repository import (
                RefreshTokenRepository,
            )
            from app.repositories.user_repository import UserRepository

            # Get dependencies
            database = self.get_core("database")
            audit = self.get_core("audit")

            # Register real repositories with database and audit
            user_repo = UserRepository(database, audit)
            self.register_repository("user", user_repo)

            email_verification_repo = EmailVerificationRepository(database, audit)
            self.register_repository("email_verification", email_verification_repo)

            refresh_token_repo = RefreshTokenRepository(database, audit)
            self.register_repository("refresh_token", refresh_token_repo)

            # For other repositories that may not exist yet, use mocks
            repository_specs = {
                "wallet": WalletRepositoryInterface,
                "historical_balance": HistoricalBalanceRepositoryInterface,
                "token": TokenRepositoryInterface,
                "password_reset": PasswordResetRepositoryInterface,
                "oauth_account": OAuthAccountRepositoryInterface,
                "portfolio_snapshot": PortfolioSnapshotRepositoryInterface,
                "token_balance": TokenBalanceRepositoryInterface,
                "token_price": TokenPriceRepositoryInterface,
            }

            for repo_name, repo_spec in repository_specs.items():
                mock_repo = Mock(spec=repo_spec)
                # Add common async mock methods
                common_methods = [
                    "create",
                    "get_by_id",
                    "get_by_email",
                    "get_by_username",
                    "update",
                    "delete",
                    "find_all",
                    "exists",
                    "get_all",
                    "get_by_user_id",
                    "get_by_address",
                    "save",
                    "remove",
                ]
                for method_name in common_methods:
                    setattr(mock_repo, method_name, AsyncMock())

                # Add repository-specific methods
                if repo_name == "password_reset":
                    setattr(mock_repo, "get_valid", AsyncMock(return_value=None))
                    setattr(mock_repo, "mark_used", AsyncMock())
                    setattr(mock_repo, "delete_expired", AsyncMock())
                elif repo_name == "email_verification":
                    setattr(mock_repo, "get_valid", AsyncMock(return_value=None))
                    setattr(mock_repo, "get_by_token", AsyncMock())
                    setattr(mock_repo, "mark_used", AsyncMock())
                    setattr(mock_repo, "delete_expired", AsyncMock())

                self.register_repository(repo_name, mock_repo)

        except ImportError:
            # Fallback to mocks if real repositories aren't available
            self._register_mock_repositories()

    def _register_mock_repositories(self):
        """Register mock repositories for unit testing."""
        # Import enhanced mocks
        from tests.shared.fixtures.enhanced_mocks import MockUserRepository

        # Special handling for user repository with enhanced mock
        enhanced_user_repo = MockUserRepository()
        self.register_repository("user", enhanced_user_repo)

        # For other repositories, use basic mocks for now
        repository_specs = {
            "email_verification": EmailVerificationRepositoryInterface,
            "wallet": WalletRepositoryInterface,
            "historical_balance": HistoricalBalanceRepositoryInterface,
            "token": TokenRepositoryInterface,
            "password_reset": PasswordResetRepositoryInterface,
            "oauth_account": OAuthAccountRepositoryInterface,
            "portfolio_snapshot": PortfolioSnapshotRepositoryInterface,
            "token_balance": TokenBalanceRepositoryInterface,
            "token_price": TokenPriceRepositoryInterface,
            "refresh_token": RefreshTokenRepositoryInterface,
        }

        for repo_name, repo_spec in repository_specs.items():
            mock_repo = Mock(spec=repo_spec)
            # Add common async mock methods that repositories typically have
            common_methods = [
                "create",
                "get_by_id",
                "get_by_email",
                "get_by_username",
                "update",
                "delete",
                "find_all",
                "exists",
                "get_all",
                "get_by_user_id",
                "get_by_address",
                "save",
                "remove",
            ]
            for method_name in common_methods:
                setattr(mock_repo, method_name, AsyncMock())

            # Add repository-specific methods
            if repo_name == "password_reset":
                setattr(mock_repo, "get_valid", AsyncMock(return_value=None))
                setattr(mock_repo, "mark_used", AsyncMock())
                setattr(mock_repo, "delete_expired", AsyncMock())
            elif repo_name == "email_verification":
                setattr(mock_repo, "get_valid", AsyncMock(return_value=None))
                setattr(mock_repo, "get_by_token", AsyncMock())
                setattr(mock_repo, "mark_used", AsyncMock())
                setattr(mock_repo, "delete_expired", AsyncMock())

            self.register_repository(repo_name, mock_repo)

    def configure_repository_mock(self, repo_name: str, **mock_behaviors: Any) -> Mock:
        """Configure specific mock behaviors for a repository.

        Args:
            repo_name: Name of the repository to configure
            **mock_behaviors: Keyword arguments defining mock behaviors

        Returns:
            The configured mock repository

        Example:
            container.configure_repository_mock(
                "user",
                get_by_id=AsyncMock(return_value=user_instance),
                create=AsyncMock(return_value=user_instance)
            )
        """
        repo = self.get_repository(repo_name)
        for method_name, behavior in mock_behaviors.items():
            setattr(repo, method_name, behavior)
        return repo

    def reset_mocks(self):
        """Reset all mocks in the container."""
        for service in self._services.values():
            if hasattr(service, "reset_mock"):
                service.reset_mock()

        for repo in self._repositories.values():
            if hasattr(repo, "reset_mock"):
                repo.reset_mock()

        for usecase in self._usecases.values():
            if hasattr(usecase, "reset_mock"):
                usecase.reset_mock()

    def _register_test_usecases(self):
        """Register mock usecases for testing."""
        # Import usecase classes (only existing ones)
        from app.usecase.auth_usecase import AuthUsecase
        from app.usecase.email_verification_usecase import (
            EmailVerificationUsecase,
        )
        from app.usecase.historical_balance_usecase import (
            HistoricalBalanceUsecase,
        )
        from app.usecase.oauth_usecase import OAuthUsecase
        from app.usecase.portfolio_snapshot_usecase import (
            PortfolioSnapshotUsecase,
        )
        from app.usecase.token_balance_usecase import TokenBalanceUsecase
        from app.usecase.token_price_usecase import TokenPriceUsecase
        from app.usecase.token_usecase import TokenUsecase
        from app.usecase.user_profile_usecase import UserProfileUsecase
        from app.usecase.wallet_usecase import WalletUsecase

        # Create usecases with proper dependency injection
        # Get required dependencies
        config = self.get_core("config")
        audit = self.get_core("audit")

        # Get repositories
        user_repo = self.get_repository("user")
        email_verification_repo = self.get_repository("email_verification")
        refresh_token_repo = self.get_repository("refresh_token")
        wallet_repo = self.get_repository("wallet")
        oauth_account_repo = self.get_repository("oauth_account")
        portfolio_snapshot_repo = self.get_repository("portfolio_snapshot")
        # Get remaining repositories (not used in current usecases but available)
        # historical_balance_repo = self.get_repository("historical_balance")
        # token_repo = self.get_repository("token")
        # token_price_repo = self.get_repository("token_price")
        # token_balance_repo = self.get_repository("token_balance")

        # Get services
        email_service = self.get_service("email")
        oauth_service = self.get_service("oauth")

        # Get utilities
        jwt_utils = self.get_utility("jwt_utils")

        # Create usecases with proper dependency injection
        try:
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
        except Exception as e:
            print(f"Failed to create AuthUsecase: {e}")
            mock_usecase = Mock(spec=AuthUsecase)
            # Add necessary mock methods
            mock_usecase.register = AsyncMock(return_value=None)
            mock_usecase.authenticate = AsyncMock()
            mock_usecase.refresh = AsyncMock()
            mock_usecase.revoke_refresh_token = AsyncMock()
            self.register_usecase("auth", mock_usecase)

        try:
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
        except Exception:
            mock_usecase = Mock(spec=EmailVerificationUsecase)
            self.register_usecase("email_verification", mock_usecase)

        try:
            oauth_uc = OAuthUsecase(
                oauth_account_repo,
                user_repo,
                refresh_token_repo,
                oauth_service,
                config,
                audit,
            )
            self.register_usecase("oauth", oauth_uc)
        except Exception:
            mock_usecase = Mock(spec=OAuthUsecase)
            self.register_usecase("oauth", mock_usecase)

        try:
            user_profile_uc = UserProfileUsecase(user_repo, audit)
            self.register_usecase("user_profile", user_profile_uc)
        except Exception:
            mock_usecase = Mock(spec=UserProfileUsecase)
            self.register_usecase("user_profile", mock_usecase)

        try:
            wallet_uc = WalletUsecase(
                wallet_repo,
                user_repo,
                portfolio_snapshot_repo,
                config,
                audit,
            )
            self.register_usecase("wallet", wallet_uc)
        except Exception:
            mock_usecase = Mock(spec=WalletUsecase)
            self.register_usecase("wallet", mock_usecase)

        # For remaining usecases, use mocks for now
        remaining_usecases = {
            "token_balance": TokenBalanceUsecase,
            "token_price": TokenPriceUsecase,
            "token": TokenUsecase,
            "historical_balance": HistoricalBalanceUsecase,
            "portfolio_snapshot": PortfolioSnapshotUsecase,
        }

        for name, usecase_class in remaining_usecases.items():
            mock_usecase = Mock(spec=usecase_class)
            self.register_usecase(name, mock_usecase)

    def _register_test_endpoints(self):
        """Register mock endpoints for testing."""
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

        # Get dependencies for endpoints
        try:
            # Admin endpoint
            user_repo = self.get_repository("user")
            admin_endpoint = Admin(user_repo)
            self.register_endpoint("admin", admin_endpoint)
        except Exception:
            mock_endpoint = Mock(spec=Admin)
            mock_endpoint.ep = Mock()
            self.register_endpoint("admin", mock_endpoint)

        try:
            # Auth endpoint
            auth_usecase = self.get_usecase("auth")
            rate_limiter_utils = self.get_utility("rate_limiter_utils")
            auth_endpoint = Auth(auth_usecase, rate_limiter_utils)
            self.register_endpoint("auth", auth_endpoint)
        except Exception:
            mock_endpoint = Mock(spec=Auth)
            mock_endpoint.ep = Mock()
            self.register_endpoint("auth", mock_endpoint)

        try:
            # DeFi endpoint
            wallet_uc = self.get_usecase("wallet")
            defi_endpoint = DeFi(wallet_uc)
            self.register_endpoint("defi", defi_endpoint)
        except Exception:
            mock_endpoint = Mock(spec=DeFi)
            mock_endpoint.ep = Mock()
            self.register_endpoint("defi", mock_endpoint)

        try:
            # Email verification endpoint
            email_verification_uc = self.get_usecase("email_verification")
            email_verification_endpoint = EmailVerification(email_verification_uc)
            self.register_endpoint("email_verification", email_verification_endpoint)
        except Exception:
            mock_endpoint = Mock(spec=EmailVerification)
            mock_endpoint.ep = Mock()
            self.register_endpoint("email_verification", mock_endpoint)

        try:
            # Health endpoint (no dependencies)
            health_endpoint = Health()
            self.register_endpoint("health", health_endpoint)
        except Exception:
            mock_endpoint = Mock(spec=Health)
            mock_endpoint.ep = Mock()
            self.register_endpoint("health", mock_endpoint)

        try:
            # JWKS endpoint (no dependencies)
            jwks_endpoint = JWKS()
            self.register_endpoint("jwks", jwks_endpoint)
        except Exception:
            mock_endpoint = Mock(spec=JWKS)
            mock_endpoint.ep = Mock()
            self.register_endpoint("jwks", mock_endpoint)

        try:
            # OAuth endpoint
            oauth_uc = self.get_usecase("oauth")
            oauth_endpoint = OAuth(oauth_uc)
            self.register_endpoint("oauth", oauth_endpoint)
        except Exception:
            mock_endpoint = Mock(spec=OAuth)
            mock_endpoint.ep = Mock()
            self.register_endpoint("oauth", mock_endpoint)

        try:
            # Password reset endpoint
            password_reset_repo = self.get_repository("password_reset")
            user_repo = self.get_repository("user")
            email_service = self.get_service("email")
            rate_limiter_utils = self.get_utility("rate_limiter_utils")
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
        except Exception:
            mock_endpoint = Mock(spec=PasswordReset)
            mock_endpoint.ep = Mock()
            self.register_endpoint("password_reset", mock_endpoint)

        try:
            # Users endpoint
            user_repo = self.get_repository("user")
            user_profile_uc = self.get_usecase("user_profile")
            file_upload_service = self.get_service("file_upload")
            users_endpoint = Users(user_repo, user_profile_uc, file_upload_service)
            self.register_endpoint("users", users_endpoint)
        except Exception:
            mock_endpoint = Mock(spec=Users)
            mock_endpoint.ep = Mock()
            self.register_endpoint("users", mock_endpoint)

        try:
            # Wallets endpoint
            wallet_uc = self.get_usecase("wallet")
            token_uc = self.get_usecase("token")
            historical_balance_uc = self.get_usecase("historical_balance")
            token_price_uc = self.get_usecase("token_price")
            token_balance_uc = self.get_usecase("token_balance")
            portfolio_snapshot_uc = self.get_usecase("portfolio_snapshot")
            wallets_endpoint = Wallets(
                wallet_uc,
                token_uc,
                historical_balance_uc,
                token_price_uc,
                token_balance_uc,
                portfolio_snapshot_uc,
            )
            self.register_endpoint("wallets", wallets_endpoint)
        except Exception:
            mock_endpoint = Mock(spec=Wallets)
            mock_endpoint.ep = Mock()
            self.register_endpoint("wallets", mock_endpoint)

    def create_integration_container(
        self, test_session: AsyncSession, test_config: Optional[Configuration] = None
    ) -> "TestDIContainer":
        """Create a new container configured for integration testing.

        Args:
            test_session: Database session for integration tests
            test_config: Optional test configuration

        Returns:
            New TestDIContainer configured for integration testing
        """
        return TestDIContainer(test_config=test_config, test_session=test_session)

    def create_unit_container(
        self, test_config: Optional[Configuration] = None
    ) -> "TestDIContainer":
        """Create a new container configured for unit testing.

        Args:
            test_config: Optional test configuration

        Returns:
            New TestDIContainer configured for unit testing
        """
        return TestDIContainer(test_config=test_config, test_session=None)
