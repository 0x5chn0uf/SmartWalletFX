"""Tests for DIContainer and core infrastructure services."""

import pytest

from app.core.config import ConfigurationService
from app.core.database import DatabaseService
from app.di import DIContainer
from app.utils.logging import Audit


class TestDIContainer:
    """Test DIContainer functionality."""

    @pytest.fixture
    def di_container(self):
        """Create a DIContainer instance for testing."""
        return DIContainer()

    def test_config_service_registration(self, di_container):
        """Test that ConfigurationService is registered."""
        config_service = di_container.get_service("config")
        assert config_service is not None
        assert hasattr(config_service, "PROJECT_NAME")
        assert hasattr(config_service, "VERSION")

    def test_database_service_registration(self, di_container):
        """Test that DatabaseService is registered."""
        database_service = di_container.get_service("database")
        assert database_service is not None
        assert hasattr(database_service, "get_session")

    def test_audit_service_registration(self, di_container):
        """Test that Audit service is registered."""
        audit_service = di_container.get_service("audit")
        assert audit_service is not None

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
            "admin_db",
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

        # Test admin_db endpoint
        admin_db_endpoint = di_container.get_endpoint("admin_db")
        assert hasattr(admin_db_endpoint, "ep")
        assert "admin" in admin_db_endpoint.ep.tags
        assert "database" in admin_db_endpoint.ep.tags

        # Test admin endpoint
        admin_endpoint = di_container.get_endpoint("admin")
        assert hasattr(admin_endpoint, "ep")
        assert "admin" in admin_endpoint.ep.tags

    def test_service_singleton_behavior(self, di_container):
        """Test that services are singletons."""
        config1 = di_container.get_service("config")
        config2 = di_container.get_service("config")
        assert config1 is config2

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

    def test_nonexistent_service_returns_none(self, di_container):
        """Test that getting a non-existent service returns None."""
        assert di_container.get_service("nonexistent") is None

    def test_nonexistent_repository_returns_none(self, di_container):
        """Test that getting a non-existent repository returns None."""
        assert di_container.get_repository("nonexistent") is None

    def test_nonexistent_usecase_returns_none(self, di_container):
        """Test that getting a non-existent usecase returns None."""
        assert di_container.get_usecase("nonexistent") is None

    def test_nonexistent_endpoint_returns_none(self, di_container):
        """Test that getting a non-existent endpoint returns None."""
        assert di_container.get_endpoint("nonexistent") is None


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


class TestDatabaseService:
    """Test the DatabaseService."""

    def test_database_service_initialization(self):
        """Test that DatabaseService initializes with proper engines and session factories."""
        config_service = ConfigurationService()
        database_service = DatabaseService(config_service)

        assert database_service.config_service is config_service
        assert hasattr(database_service, "async_engine")
        assert hasattr(database_service, "sync_engine")
        assert hasattr(database_service, "async_session_factory")
        assert hasattr(database_service, "sync_session_factory")

    def test_sync_session_creation(self):
        """Test that sync session can be created."""
        config_service = ConfigurationService()
        database_service = DatabaseService(config_service)

        sync_session = database_service.get_sync_session()
        assert sync_session is not None
        sync_session.close()

    @pytest.mark.asyncio
    async def test_async_session_creation(self):
        """Test that async session can be created."""
        config_service = ConfigurationService()
        database_service = DatabaseService(config_service)

        async with database_service.get_session() as session:
            assert session is not None
