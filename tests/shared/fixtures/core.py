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
    """Mock Configuration for testing."""
    mock = Mock()
    mock.database_url = "sqlite+aiosqlite:///:memory:"
    mock.sync_database_url = "sqlite:///:memory:"
    mock.PROJECT_NAME = "Test App"
    mock.VERSION = "1.0.0"
    mock.JWT_SECRET_KEY = "test-jwt-secret"
    mock.JWT_ALGORITHM = "HS256"
    mock.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock.REFRESH_TOKEN_EXPIRE_DAYS = 7
    mock.REDIS_URL = "redis://localhost:6379/1"
    mock.EMAIL_FROM = "test@example.com"
    mock.LOG_LEVEL = "INFO"
    mock.JWT_ROTATION_SCHEDULE_CRON = "0 2 * * *"
    mock.ACTIVE_JWT_KID = "test-kid"
    mock.EMAIL_VERIFICATION_EXPIRE_MINUTES = 1440
    mock.FRONTEND_BASE_URL = "http://test-frontend.com"
    mock.JWT_KEYS = None
    mock.JWT_PRIVATE_KEY_PATH = None
    mock.JWT_PUBLIC_KEY_PATH = None
    mock.JWT_ROTATION_GRACE_PERIOD_SECONDS = 60
    mock.JWT_SIGNING_KEY_ROTATION_MINUTES = 60
    mock.ARBITRUM_RPC_URL = "http://mock-rpc"
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
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.merge = AsyncMock()
        session.delete = AsyncMock()
        session.rollback = AsyncMock()
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
def mock_session():
    """Mock database session for testing."""
    from unittest.mock import AsyncMock, Mock

    session = Mock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.merge = AsyncMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    return session


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
    """Mock JWT utilities for testing."""
    from unittest.mock import AsyncMock

    mock = Mock()
    mock.generate_jwt = Mock()
    mock.verify_jwt = Mock()
    mock.decode_jwt = Mock()
    mock.create_access_token = Mock()
    mock.create_refresh_token = Mock()
    mock.verify_token = AsyncMock()
    return mock
