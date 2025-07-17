"""Tests for DIContainer and core infrastructure services."""

import pytest

from app.core.config import ConfigurationService
from app.core.database import CoreDatabase
from app.di import DIContainer


class TestDIContainer:
    """Test DIContainer functionality."""

    @pytest.fixture
    def di_container(self):
        """Create a DIContainer instance for testing."""
        return DIContainer()

    def test_config_service_registration(self, di_container):
        """Test that ConfigurationService is registered."""
        config = di_container.get_core("config")
        assert config is not None
        assert hasattr(config, "PROJECT_NAME")
        assert hasattr(config, "VERSION")

    def test_database_registration(self, di_container):
        """Test that CoreDatabase is registered."""
        database = di_container.get_core("database")
        assert database is not None
        assert hasattr(database, "get_session")

    def test_audit_service_registration(self, di_container):
        """Test that Audit service is registered."""
        audit = di_container.get_core("audit")
        assert audit is not None

    def test_helper_services_registration(self, di_container):
        """Test that all helper services are registered."""
        # Test that all helper services are registered
        assert di_container.get_core("logging") is not None
        assert di_container.get_core("celery") is not None
        assert di_container.get_core("error_handling") is not None
        assert di_container.get_core("middleware") is not None
        assert di_container.get_core("database") is not None

    def test_helper_service_types(self, di_container):
        """Test that helper services are of correct types."""
        from app.core.celery import CoreCelery
        from app.core.database import CoreDatabase
        from app.core.error_handling import CoreErrorHandling
        from app.core.logging import CoreLogging
        from app.core.middleware import Middleware

        logging = di_container.get_core("logging")
        assert isinstance(logging, CoreLogging)

        celery = di_container.get_core("celery")
        assert isinstance(celery, CoreCelery)

        error_handling = di_container.get_core("error_handling")
        assert isinstance(error_handling, CoreErrorHandling)

        middleware = di_container.get_core("middleware")
        assert isinstance(middleware, Middleware)

        database = di_container.get_core("database")
        assert isinstance(database, CoreDatabase)

    def test_helper_service_dependencies(self, di_container):
        """Test that helper services have proper dependencies injected."""
        # Test LoggingService has config dependency
        logging = di_container.get_core("logging")
        config = di_container.get_core("config")
        assert logging.config_service == config

        # Test CeleryService has config dependency
        celery = di_container.get_core("celery")
        assert celery.config_service == config

        # Test ErrorHandlingService has audit dependency
        error_handling = di_container.get_core("error_handling")
        audit = di_container.get_core("audit")
        assert error_handling.audit == audit

        # Test MiddlewareService has audit dependency
        middleware = di_container.get_core("middleware")
        assert middleware.audit == audit

        # Test DatabaseInitializationService has database and audit dependencies
        database = di_container.get_core("database")
        audit = di_container.get_core("audit")
        assert database.audit == audit

    def test_all_repositories_registered(self, di_container):
        """Test that all repositories are registered."""
        expected_repositories = [
            "user",
            "email_verification",
            "oauth_account",
            "password_reset",
            "refresh_token",
            "wallet",
            "portfolio_snapshot",
            "historical_balance",
            "token",
            "token_price",
            "token_balance",
        ]

        for repo_name in expected_repositories:
            repo = di_container.get_repository(repo_name)
            assert repo is not None, f"Repository '{repo_name}' not registered"

    def test_all_usecases_registered(self, di_container):
        """Test that all usecases are registered."""
        expected_usecases = [
            "email_verification",
            "wallet",
            "oauth",
            "token_price",
            "token",
            "historical_balance",
            "token_balance",
            "portfolio_snapshot",
        ]

        for usecase_name in expected_usecases:
            usecase = di_container.get_usecase(usecase_name)
            assert usecase is not None, f"Usecase '{usecase_name}' not registered"

    def test_all_endpoints_registered(self, di_container):
        """Test that all endpoints are registered."""
        expected_endpoints = [
            "email_verification",
            "oauth",
            "wallets",
            "health",
            "jwks",
            "users",
            "admin",
        ]

        for endpoint_name in expected_endpoints:
            endpoint = di_container.get_endpoint(endpoint_name)
            assert endpoint is not None, f"Endpoint '{endpoint_name}' not registered"

    def test_endpoint_dependency_injection(self, di_container):
        """Test that endpoints have proper dependency injection."""
        # Test email verification endpoint
        email_verification_endpoint = di_container.get_endpoint("email_verification")
        assert hasattr(email_verification_endpoint, "ep")
        assert email_verification_endpoint.ep.prefix == "/auth"

        # Test OAuth endpoint
        oauth_endpoint = di_container.get_endpoint("oauth")
        assert hasattr(oauth_endpoint, "ep")
        assert oauth_endpoint.ep.prefix == "/auth/oauth"

        # Test wallets endpoint
        wallets_endpoint = di_container.get_endpoint("wallets")
        assert hasattr(wallets_endpoint, "ep")
        assert "wallets" in wallets_endpoint.ep.tags

        # Test health endpoint
        health_endpoint = di_container.get_endpoint("health")
        assert hasattr(health_endpoint, "ep")
        assert "health" in health_endpoint.ep.tags

        # Test JWKS endpoint
        jwks_endpoint = di_container.get_endpoint("jwks")
        assert hasattr(jwks_endpoint, "ep")
        assert "jwks" in jwks_endpoint.ep.tags

        # Test users endpoint
        users_endpoint = di_container.get_endpoint("users")
        assert hasattr(users_endpoint, "ep")
        assert users_endpoint.ep.prefix == "/users"

        # Test admin endpoint
        admin_endpoint = di_container.get_endpoint("admin")
        assert hasattr(admin_endpoint, "ep")
        assert "admin" in admin_endpoint.ep.tags

    def test_service_singleton_behavior(self, di_container):
        """Test that services are singletons."""
        config1 = di_container.get_core("config")
        config2 = di_container.get_core("config")
        assert config1 is config2

    def test_helper_service_singleton_behavior(self, di_container):
        """Test that helper services are singletons."""
        # Test that multiple calls return the same instance
        logging_service1 = di_container.get_core("logging")
        logging_service2 = di_container.get_core("logging")
        assert logging_service1 is logging_service2

        celery_service1 = di_container.get_core("celery")
        celery_service2 = di_container.get_core("celery")
        assert celery_service1 is celery_service2

        error_handling_service1 = di_container.get_core("error_handling")
        error_handling_service2 = di_container.get_core("error_handling")
        assert error_handling_service1 is error_handling_service2

        middleware_service1 = di_container.get_core("middleware")
        middleware_service2 = di_container.get_core("middleware")
        assert middleware_service1 is middleware_service2

        database_init_service1 = di_container.get_core("database")
        database_init_service2 = di_container.get_core("database")
        assert database_init_service1 is database_init_service2

    def test_repository_singleton_behavior(self, di_container):
        """Test that repositories are singletons."""
        user_repo1 = di_container.get_repository("user")
        user_repo2 = di_container.get_repository("user")
        assert user_repo1 is user_repo2

    def test_usecase_singleton_behavior(self, di_container):
        """Test that usecases are singletons."""
        wallet_uc1 = di_container.get_usecase("wallet")
        wallet_uc2 = di_container.get_usecase("wallet")
        assert wallet_uc1 is wallet_uc2

    def test_endpoint_singleton_behavior(self, di_container):
        """Test that endpoints are singletons."""
        email_verification_endpoint1 = di_container.get_endpoint("email_verification")
        email_verification_endpoint2 = di_container.get_endpoint("email_verification")
        assert email_verification_endpoint1 is email_verification_endpoint2

    def test_nonexistent_service_raises_error(self, di_container):
        """Test that getting a non-existent service raises ValueError."""
        with pytest.raises(ValueError, match="Service 'nonexistent' not found"):
            di_container.get_service("nonexistent")

    def test_nonexistent_repository_raises_error(self, di_container):
        """Test that getting a non-existent repository raises ValueError."""
        with pytest.raises(ValueError, match="Repository 'nonexistent' not found"):
            di_container.get_repository("nonexistent")

    def test_nonexistent_usecase_raises_error(self, di_container):
        """Test that getting a non-existent usecase raises ValueError."""
        with pytest.raises(ValueError, match="Usecase 'nonexistent' not found"):
            di_container.get_usecase("nonexistent")

    def test_nonexistent_endpoint_raises_error(self, di_container):
        """Test that getting a non-existent endpoint raises ValueError."""
        with pytest.raises(ValueError, match="Endpoint 'nonexistent' not found"):
            di_container.get_endpoint("nonexistent")

    def test_repository_dependency_injection_validation(self, di_container):
        """Test that repositories have proper dependency injection."""
        # Test that all repositories have database and audit dependencies
        expected_repositories = [
            "user",
            "email_verification",
            "oauth_account",
            "password_reset",
            "refresh_token",
            "wallet",
            "portfolio_snapshot",
            "historical_balance",
            "token",
            "token_price",
            "token_balance",
        ]

        for repo_name in expected_repositories:
            repo = di_container.get_repository(repo_name)
            # Check that repositories have some form of database and audit dependencies
            # Different repositories may use different naming conventions
            class_name = repo.__class__.__name__

            # Check for database dependency
            has_database = hasattr(repo, f"_{class_name}__database")
            assert has_database, f"Repository '{repo_name}' missing database dependency"

            # Check for audit dependency
            assert hasattr(
                repo, f"_{class_name}__audit"
            ), f"Repository '{repo_name}' missing audit dependency"

    def test_usecase_dependency_injection_validation(self, di_container):
        """Test that usecases have proper dependency injection."""
        # Test that all usecases have required dependencies
        expected_usecases = [
            "email_verification",
            "wallet",
            "oauth",
            "token_price",
            "token",
            "historical_balance",
            "token_balance",
            "portfolio_snapshot",
        ]

        for usecase_name in expected_usecases:
            usecase = di_container.get_usecase(usecase_name)

            # All usecases should have audit (using Python name mangling)
            assert hasattr(
                usecase, f"_{usecase.__class__.__name__}__audit"
            ), f"Usecase '{usecase_name}' missing audit"

            # Most usecases have config_service, but portfolio_snapshot doesn't
            if usecase_name != "portfolio_snapshot":
                assert hasattr(
                    usecase, f"_{usecase.__class__.__name__}__config_service"
                ), f"Usecase '{usecase_name}' missing config_service"

    def test_endpoint_router_configuration(self, di_container):
        """Test that endpoints have proper router configuration."""
        # Test specific endpoint configurations
        endpoints_config = {
            "email_verification": {"prefix": "/auth", "tags": ["auth"]},
            "oauth": {"prefix": "/auth/oauth", "tags": ["auth"]},
            "wallets": {"tags": ["wallets"]},
            "health": {"tags": ["health"]},
            "jwks": {"tags": ["jwks"]},
            "users": {"prefix": "/users", "tags": ["users"]},
            "admin": {"tags": ["admin"]},
        }

        for endpoint_name, config in endpoints_config.items():
            endpoint = di_container.get_endpoint(endpoint_name)
            assert endpoint is not None, f"Endpoint '{endpoint_name}' not found"
            assert hasattr(endpoint, "ep"), f"Endpoint '{endpoint_name}' missing router"

            # Check prefix if specified
            if "prefix" in config:
                assert (
                    endpoint.ep.prefix == config["prefix"]
                ), f"Endpoint '{endpoint_name}' has wrong prefix"

            # Check tags if specified
            if "tags" in config:
                for tag in config["tags"]:
                    assert (
                        tag in endpoint.ep.tags
                    ), f"Endpoint '{endpoint_name}' missing tag '{tag}'"

    def test_service_initialization_order(self, di_container):
        """Test that services are initialized in the correct order."""
        # Core services should be initialized first
        config = di_container.get_core("config")
        database = di_container.get_core("database")
        audit = di_container.get_core("audit")

        # These should all be available
        assert config is not None
        assert database is not None
        assert audit is not None

        # Helper services should depend on core services
        logging_service = di_container.get_core("logging")
        celery_service = di_container.get_core("celery")

        assert logging_service is not None
        assert celery_service is not None

    def test_repository_types_validation(self, di_container):
        """Test that repositories are of correct types."""
        from app.repositories.email_verification_repository import (
            EmailVerificationRepository,
        )
        from app.repositories.historical_balance_repository import (
            HistoricalBalanceRepository,
        )
        from app.repositories.oauth_account_repository import (
            OAuthAccountRepository,
        )
        from app.repositories.password_reset_repository import (
            PasswordResetRepository,
        )
        from app.repositories.portfolio_snapshot_repository import (
            PortfolioSnapshotRepository,
        )
        from app.repositories.refresh_token_repository import (
            RefreshTokenRepository,
        )
        from app.repositories.token_balance_repository import (
            TokenBalanceRepository,
        )
        from app.repositories.token_price_repository import (
            TokenPriceRepository,
        )
        from app.repositories.token_repository import TokenRepository
        from app.repositories.user_repository import UserRepository
        from app.repositories.wallet_repository import WalletRepository

        # Test repository types
        assert isinstance(di_container.get_repository("user"), UserRepository)
        assert isinstance(di_container.get_repository("wallet"), WalletRepository)
        assert isinstance(
            di_container.get_repository("email_verification"),
            EmailVerificationRepository,
        )
        assert isinstance(
            di_container.get_repository("oauth_account"), OAuthAccountRepository
        )
        assert isinstance(
            di_container.get_repository("password_reset"), PasswordResetRepository
        )
        assert isinstance(
            di_container.get_repository("refresh_token"), RefreshTokenRepository
        )
        assert isinstance(
            di_container.get_repository("portfolio_snapshot"),
            PortfolioSnapshotRepository,
        )
        assert isinstance(
            di_container.get_repository("historical_balance"),
            HistoricalBalanceRepository,
        )
        assert isinstance(di_container.get_repository("token"), TokenRepository)
        assert isinstance(
            di_container.get_repository("token_price"), TokenPriceRepository
        )
        assert isinstance(
            di_container.get_repository("token_balance"), TokenBalanceRepository
        )

    def test_usecase_types_validation(self, di_container):
        """Test that usecases are of correct types."""
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
        from app.usecase.wallet_usecase import WalletUsecase

        # Test usecase types
        assert isinstance(
            di_container.get_usecase("email_verification"), EmailVerificationUsecase
        )
        assert isinstance(di_container.get_usecase("wallet"), WalletUsecase)
        assert isinstance(di_container.get_usecase("oauth"), OAuthUsecase)
        assert isinstance(di_container.get_usecase("token_price"), TokenPriceUsecase)
        assert isinstance(di_container.get_usecase("token"), TokenUsecase)
        assert isinstance(
            di_container.get_usecase("historical_balance"), HistoricalBalanceUsecase
        )
        assert isinstance(
            di_container.get_usecase("token_balance"), TokenBalanceUsecase
        )
        assert isinstance(
            di_container.get_usecase("portfolio_snapshot"), PortfolioSnapshotUsecase
        )

    def test_endpoint_types_validation(self, di_container):
        """Test that endpoints are of correct types."""
        from app.api.endpoints.admin import Admin
        from app.api.endpoints.email_verification import EmailVerification
        from app.api.endpoints.health import Health
        from app.api.endpoints.jwks import JWKS
        from app.api.endpoints.oauth import OAuth
        from app.api.endpoints.users import Users
        from app.api.endpoints.wallets import Wallets

        # Test endpoint types
        assert isinstance(
            di_container.get_endpoint("email_verification"), EmailVerification
        )
        assert isinstance(di_container.get_endpoint("oauth"), OAuth)
        assert isinstance(di_container.get_endpoint("wallets"), Wallets)
        assert isinstance(di_container.get_endpoint("health"), Health)
        assert isinstance(di_container.get_endpoint("jwks"), JWKS)
        assert isinstance(di_container.get_endpoint("users"), Users)
        assert isinstance(di_container.get_endpoint("admin"), Admin)

    def test_di_container_state_isolation(self):
        """Test that multiple DIContainer instances are isolated."""
        # Create two separate DIContainer instances
        di_container1 = DIContainer()
        di_container2 = DIContainer()

        # Services should be different instances between containers
        config1 = di_container1.get_core("config")
        config2 = di_container2.get_core("config")

        # While they're both ConfigurationService instances, they should be different objects
        assert config1 is not config2

        # But within the same container, they should be the same (singleton)
        config1_again = di_container1.get_core("config")
        assert config1 is config1_again

    def test_all_registered_services_are_accessible(self, di_container):
        """Test that all registered services can be accessed."""
        # Core services
        assert di_container.get_core("config") is not None
        assert di_container.get_core("database") is not None
        assert di_container.get_core("audit") is not None

        # Helper services
        assert di_container.get_core("logging") is not None
        assert di_container.get_core("celery") is not None
        assert di_container.get_core("error_handling") is not None
        assert di_container.get_core("middleware") is not None
        assert di_container.get_core("database") is not None

    def test_all_registered_repositories_are_accessible(self, di_container):
        """Test that all registered repositories can be accessed."""
        expected_repositories = [
            "user",
            "email_verification",
            "oauth_account",
            "password_reset",
            "refresh_token",
            "wallet",
            "portfolio_snapshot",
            "historical_balance",
            "token",
            "token_price",
            "token_balance",
        ]

        for repo_name in expected_repositories:
            assert (
                di_container.get_repository(repo_name) is not None
            ), f"Repository '{repo_name}' not accessible"

    def test_all_registered_usecases_are_accessible(self, di_container):
        """Test that all registered usecases can be accessed."""
        expected_usecases = [
            "email_verification",
            "wallet",
            "oauth",
            "token_price",
            "token",
            "historical_balance",
            "token_balance",
            "portfolio_snapshot",
        ]

        for usecase_name in expected_usecases:
            assert (
                di_container.get_usecase(usecase_name) is not None
            ), f"Usecase '{usecase_name}' not accessible"

    def test_all_registered_endpoints_are_accessible(self, di_container):
        """Test that all registered endpoints can be accessed."""
        expected_endpoints = [
            "email_verification",
            "oauth",
            "wallets",
            "health",
            "jwks",
            "users",
            "admin",
        ]

        for endpoint_name in expected_endpoints:
            assert (
                di_container.get_endpoint(endpoint_name) is not None
            ), f"Endpoint '{endpoint_name}' not accessible"


class TestConfigurationService:
    """Test the ConfigurationService."""

    def test_configuration_service_properties(self):
        """Test that ConfigurationService properties work correctly."""
        config_service = ConfigurationService()

        # Test direct attribute access
        assert config_service.PROJECT_NAME == "SmartWalletFX"
        assert config_service.VERSION == "0.1.0"
        assert config_service.ENVIRONMENT == "development"
        assert isinstance(config_service.BACKEND_CORS_ORIGINS, list)
        assert config_service.ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert config_service.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_configuration_service_is_pydantic_settings(self):
        """Test that ConfigurationService is still a proper Pydantic BaseSettings."""
        config_service = ConfigurationService()

        # Should have Pydantic BaseSettings functionality
        assert hasattr(config_service, "model_config")
        assert hasattr(config_service, "model_dump")
        assert hasattr(config_service, "model_validate")


class TestCoreDatabase:
    """Test the CoreDatabase."""

    @pytest.fixture
    def di_container(self):
        """Create a DIContainer instance for testing."""
        return DIContainer()

    def test_database_initialization(self, di_container):
        """Test that CoreDatabase initializes with proper engines and session factories."""
        config = di_container.get_core("config")
        audit = di_container.get_core("audit")
        database = CoreDatabase(config, audit)

        assert database.config_service is config
        assert hasattr(database, "async_engine")
        assert hasattr(database, "sync_engine")
        assert hasattr(database, "async_session_factory")
        assert hasattr(database, "sync_session_factory")

    def test_sync_session_creation(self, di_container):
        """Test that sync session can be created."""
        config = di_container.get_core("config")
        audit = di_container.get_core("audit")
        database = CoreDatabase(config, audit)

        sync_session = database.get_sync_session()
        assert sync_session is not None
        sync_session.close()

    @pytest.mark.asyncio
    async def test_async_session_creation(self, di_container):
        """Test that async session can be created."""
        config = di_container.get_core("config")
        audit = di_container.get_core("audit")
        database = CoreDatabase(config, audit)

        async with database.get_session() as session:
            assert session is not None
