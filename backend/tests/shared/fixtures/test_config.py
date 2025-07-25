"""
Test Configuration Management.

This module provides test-specific configurations for different testing scenarios:
1. Unit test configuration (fast, mocked)
2. Integration test configuration (real database)
3. Performance test configuration (optimized settings)
4. Security test configuration (specific security settings)
"""

import os

import pytest

from app.core.config import Configuration


class TestConfiguration(Configuration):
    """Test-specific configuration with optimized defaults."""

    def __init__(self, **overrides):
        """Initialize test configuration with test-optimized defaults."""
        # Set test environment before calling super().__init__()
        # Always force the environment to 'testing' for predictable behaviour
        os.environ["ENVIRONMENT"] = "testing"

        # Set test-optimized defaults
        test_defaults = {
            "BCRYPT_ROUNDS": 4,  # Fast hashing for tests
            "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
            "REFRESH_TOKEN_EXPIRE_DAYS": 1,
            "EMAIL_VERIFICATION_EXPIRE_HOURS": 1,
            "PASSWORD_RESET_EXPIRE_HOURS": 1,
            "JWT_ROTATION_GRACE_PERIOD_SECONDS": 60,
            "RATE_LIMIT_ENABLED": False,  # Disable rate limiting in tests
            "LOG_LEVEL": "WARNING",  # Reduce log noise in tests
            "CELERY_TASK_ALWAYS_EAGER": True,  # Execute tasks synchronously
            "FRONTEND_BASE_URL": "http://localhost:3000",  # Add frontend URL for tests
        }

        # Apply test defaults (override environment for deterministic tests)
        for key, value in test_defaults.items():
            if key not in overrides:
                os.environ[key] = str(value)

        # Apply custom overrides
        for key, value in overrides.items():
            os.environ[key] = str(value)

        super().__init__()


class UnitTestConfiguration(TestConfiguration):
    """Configuration optimized for unit tests."""

    def __init__(self, **overrides):
        unit_test_defaults = {
            "DATABASE_URL": "sqlite+aiosqlite:///test.db",
            "REDIS_URL": "redis://localhost:6379/15",  # Separate test Redis DB
            "EMAIL_ENABLED": False,
            "CELERY_BROKER_URL": "memory://",  # In-memory broker for tests
            "CELERY_RESULT_BACKEND": "memory://",
        }
        unit_test_defaults.update(overrides)
        super().__init__(**unit_test_defaults)


class IntegrationTestConfiguration(TestConfiguration):
    """Configuration for integration tests with real database."""

    def __init__(self, test_db_url: str, **overrides):
        integration_defaults = {
            "DATABASE_URL": test_db_url,
            "REDIS_URL": "redis://localhost:6379/14",  # Separate test Redis DB
            "EMAIL_ENABLED": True,  # Test email functionality
            "CELERY_TASK_ALWAYS_EAGER": True,  # Still synchronous in tests
        }
        integration_defaults.update(overrides)
        super().__init__(**integration_defaults)


class MockConfiguration:
    """Mock configuration for lightweight unit tests."""

    def __init__(self, **attributes):
        """Create mock configuration with specified attributes."""
        defaults = {
            "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
            "JWT_ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 15,
            "JWT_KEYS": {"test": "test-secret-key-for-unit-tests"},
            "ACTIVE_JWT_KID": "test",
            "BCRYPT_ROUNDS": 4,
            "REDIS_URL": "redis://localhost:6379/15",
            "EMAIL_ENABLED": False,
            "LOG_LEVEL": "ERROR",
            "RATE_LIMIT_ENABLED": False,
            "FRONTEND_BASE_URL": "http://localhost:3000",
        }
        defaults.update(attributes)

        for key, value in defaults.items():
            setattr(self, key, value)


# Configuration factory functions
def create_unit_test_config(**overrides) -> UnitTestConfiguration:
    """Create configuration optimized for unit tests."""
    return UnitTestConfiguration(**overrides)


def create_integration_test_config(
    test_db_url: str, **overrides
) -> IntegrationTestConfiguration:
    """Create configuration for integration tests."""
    return IntegrationTestConfiguration(test_db_url, **overrides)


def create_mock_config(**attributes) -> MockConfiguration:
    """Create mock configuration for lightweight tests."""
    return MockConfiguration(**attributes)


# Pytest fixtures
@pytest.fixture
def unit_test_config():
    """Provide unit test configuration."""
    return create_unit_test_config()


@pytest.fixture
def mock_config():
    """Provide mock configuration for unit tests."""
    return create_mock_config()


@pytest.fixture
def config_with_jwt():
    """Provide configuration with real JWT settings."""
    return create_mock_config(
        JWT_KEYS={
            "test-key-1": "test-secret-key-1-very-long-for-security",
            "test-key-2": "test-secret-key-2-very-long-for-security",
        },
        ACTIVE_JWT_KID="test-key-1",
        JWT_ALGORITHM="HS256",
    )


@pytest.fixture
def config_with_bcrypt():
    """Provide configuration with bcrypt settings."""
    return create_mock_config(BCRYPT_ROUNDS=4)


@pytest.fixture
def config_with_email():
    """Provide configuration with email enabled."""
    return create_mock_config(
        EMAIL_ENABLED=True,
        SMTP_HOST="smtp.example.com",
        SMTP_PORT=587,
        SMTP_USERNAME="test@example.com",
        SMTP_PASSWORD="test-password",
    )


@pytest.fixture
def config_with_redis():
    """Provide configuration with Redis settings."""
    return create_mock_config(
        REDIS_URL="redis://localhost:6379/15",
        RATE_LIMIT_ENABLED=True,
    )


@pytest.fixture
def performance_test_config():
    """Provide configuration optimized for performance tests."""
    return create_unit_test_config(
        BCRYPT_ROUNDS=1,  # Minimal hashing for performance tests
        LOG_LEVEL="CRITICAL",  # Minimal logging
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
    )


@pytest.fixture
def security_test_config():
    """Provide configuration for security-focused tests."""
    return create_mock_config(
        BCRYPT_ROUNDS=12,  # Full security rounds
        JWT_KEYS={"secure-key": "very-long-secure-secret-key-for-security-tests" * 2},
        ACTIVE_JWT_KID="secure-key",
        ACCESS_TOKEN_EXPIRE_MINUTES=5,  # Short expiry for security tests
        RATE_LIMIT_ENABLED=True,
    )


# Environment-based configuration selection
def get_test_config_for_environment() -> Configuration:
    """Get appropriate test configuration based on environment variables."""
    test_type = os.getenv("TEST_TYPE", "unit")

    if test_type == "unit":
        return create_unit_test_config()
    elif test_type == "integration":
        test_db_url = os.getenv("TEST_DB_URL")
        if not test_db_url:
            raise ValueError("TEST_DB_URL required for integration tests")
        return create_integration_test_config(test_db_url)
    elif test_type == "performance":
        return create_unit_test_config(BCRYPT_ROUNDS=1, LOG_LEVEL="CRITICAL")
    else:
        raise ValueError(f"Unknown test type: {test_type}")


# Configuration validation helpers
def validate_test_config(config: Configuration) -> bool:
    """Validate that configuration is suitable for testing."""
    checks = [
        config.BCRYPT_ROUNDS <= 6,  # Fast enough for tests
        "test" in config.DATABASE_URL.lower()
        or ":memory:" in config.DATABASE_URL,  # Test database
        config.LOG_LEVEL in ["WARNING", "ERROR", "CRITICAL"],  # Minimal logging
    ]
    return all(checks)


def assert_test_config_safety(config: Configuration):
    """Assert that configuration is safe for testing (won't affect production)."""
    if not validate_test_config(config):
        raise AssertionError("Configuration is not safe for testing environment")

    # Additional safety checks
    if "production" in config.DATABASE_URL.lower():
        raise AssertionError("Test configuration should not use production database")

    if hasattr(config, "EMAIL_ENABLED") and config.EMAIL_ENABLED:
        if not any(
            test_domain in getattr(config, "SMTP_HOST", "")
            for test_domain in ["example.com", "test.com", "localhost"]
        ):
            raise AssertionError(
                "Test configuration should not use production email settings"
            )
