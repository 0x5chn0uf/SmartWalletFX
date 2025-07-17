"""
Core service fixtures for testing.

This module provides fixtures for testing core services and utilities,
including mock services and utilities with dependency injection.
"""

from unittest.mock import Mock

import pytest

# === MOCK CORE SERVICE FIXTURES ===


@pytest.fixture
def mock_config():
    """Mock ConfigurationService for testing."""
    mock = Mock()
    mock.database_url = "sqlite+aiosqlite:///:memory:"
    mock.sync_database_url = "sqlite:///:memory:"
    mock.PROJECT_NAME = "Test App"
    mock.VERSION = "1.0.0"
    mock.JWT_SECRET_KEY = "test-jwt-secret"
    mock.JWT_ALGORITHM = "HS256"
    mock.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    mock.REDIS_URL = "redis://localhost:6379/1"
    mock.EMAIL_FROM = "test@example.com"
    mock.LOG_LEVEL = "INFO"
    mock.JWT_ROTATION_SCHEDULE_CRON = "0 2 * * *"
    return mock


@pytest.fixture
def mock_database():
    """Mock CoreDatabase for testing."""
    from contextlib import asynccontextmanager
    from unittest.mock import AsyncMock, Mock

    mock = Mock()

    # Create a proper async context manager mock for get_session
    @asynccontextmanager
    async def mock_get_session():
        session = AsyncMock()
        yield session

    mock.get_session = mock_get_session
    mock.async_engine = Mock()
    mock.sync_engine = Mock()
    return mock


@pytest.fixture
def mock_audit():
    """Mock Audit service for testing."""
    mock = Mock()
    mock.info = Mock()
    mock.warning = Mock()
    mock.error = Mock()
    mock.debug = Mock()
    return mock


@pytest.fixture
def mock_email_service():
    """Mock EmailService for testing."""
    from unittest.mock import AsyncMock

    mock = Mock()
    mock.send_email = AsyncMock()
    mock.send_verification_email = AsyncMock()
    mock.send_password_reset_email = AsyncMock()
    return mock


@pytest.fixture
def mock_jwt_utils():
    """Mock JWTUtils for testing."""
    mock = Mock()
    mock.create_access_token = Mock()
    mock.create_refresh_token = Mock()
    mock.verify_token = Mock()
    mock.decode_token = Mock()
    mock.get_current_user = Mock()
    return mock


@pytest.fixture
def mock_logging():
    """Mock CoreLogging for testing."""
    mock = Mock()
    mock.setup_logging = Mock()
    mock.get_logger = Mock()
    return mock


@pytest.fixture
def mock_celery():
    """Mock CoreCelery for testing."""
    mock = Mock()
    mock.app = Mock()
    mock.get_celery_app = Mock()
    return mock


@pytest.fixture
def mock_error_handling():
    """Mock CoreErrorHandling for testing."""
    mock = Mock()
    mock.handle_generic_exception = Mock()
    mock.handle_http_exception = Mock()
    mock.handle_validation_exception = Mock()
    return mock


@pytest.fixture
def mock_middleware():
    """Mock CoreMiddleware for testing."""
    mock = Mock()
    mock.get_correlation_id_middleware = Mock()
    mock.create_correlation_id_middleware = Mock()
    return mock


@pytest.fixture
def mock_database_initialization():
    """Mock CoreDatabase for testing."""
    from unittest.mock import AsyncMock

    mock = Mock()
    mock.init_db = AsyncMock()
    mock.create_tables = AsyncMock()
    return mock
