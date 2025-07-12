"""Tests for DIContainer and core infrastructure services."""

import pytest

from app.core.config import ConfigurationService
from app.core.database import DatabaseService
from app.di import DIContainer
from app.utils.logging import Audit


class TestDIContainer:
    """Test the DIContainer singleton management."""

    def test_container_initialization(self):
        """Test that DIContainer initializes successfully."""
        container = DIContainer()
        assert container is not None
        assert hasattr(container, "_services")
        assert hasattr(container, "_repositories")
        assert hasattr(container, "_usecases")
        assert hasattr(container, "_endpoints")

    def test_config_service_registration(self):
        """Test that ConfigurationService is properly registered."""
        container = DIContainer()
        config_service = container.get_service("config")

        assert config_service is not None
        assert isinstance(config_service, ConfigurationService)
        assert config_service.PROJECT_NAME == "SmartWalletFX"

    def test_database_service_registration(self):
        """Test that DatabaseService is properly registered."""
        container = DIContainer()
        database_service = container.get_service("database")

        assert database_service is not None
        assert isinstance(database_service, DatabaseService)
        assert hasattr(database_service, "async_engine")
        assert hasattr(database_service, "sync_engine")
        assert hasattr(database_service, "async_session_factory")
        assert hasattr(database_service, "sync_session_factory")

    def test_audit_service_registration(self):
        """Test that Audit service is properly registered."""
        container = DIContainer()
        audit_service = container.get_service("audit")

        assert audit_service is not None

    def test_all_repositories_registered(self):
        """Test that all repositories are properly registered."""
        container = DIContainer()

        # List of all expected repositories
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
            repo = container.get_repository(repo_name)
            assert repo is not None, f"Repository '{repo_name}' should be registered"

    def test_all_usecases_registered(self):
        """Test that all usecases are properly registered."""
        container = DIContainer()

        # List of all expected usecases
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
            usecase = container.get_usecase(usecase_name)
            assert usecase is not None, f"Usecase '{usecase_name}' should be registered"

    def test_singleton_behavior(self):
        """Test that services are singletons."""
        container1 = DIContainer()
        container2 = DIContainer()

        # Each container creates its own instances
        config1 = container1.get_service("config")
        container2.get_service("config")  # Just ensure it works

        # But within the same container, services should be the same instance
        config1_again = container1.get_service("config")
        assert config1 is config1_again

    def test_service_registration_methods(self):
        """Test that service registration methods work correctly."""
        container = DIContainer()

        # Test registering a new service
        test_service = "test_service_instance"
        container.register_service("test", test_service)

        retrieved_service = container.get_service("test")
        assert retrieved_service == test_service

    def test_missing_service_returns_none(self):
        """Test that requesting a non-existent service returns None."""
        container = DIContainer()

        missing_service = container.get_service("non_existent")
        assert missing_service is None


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
