"""
Repository fixtures for testing.

This module provides fixtures for testing repositories with dependency injection,
including both mock repositories and real repositories with mocked dependencies.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest

# === HELPER FUNCTIONS ===


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    repository._UserRepository__database.get_session = mock_get_session


# === MOCK REPOSITORY FIXTURES ===


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository with common async methods."""
    mock = Mock()
    mock.get_by_id = AsyncMock()
    mock.get_by_email = AsyncMock()
    mock.get_by_username = AsyncMock()
    mock.exists = AsyncMock()
    mock.save = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_email_verification_repository():
    """Mock EmailVerificationRepository with common async methods."""
    mock = Mock()
    mock.create = AsyncMock()
    mock.get_by_token = AsyncMock()
    mock.mark_used = AsyncMock()
    mock.delete_expired = AsyncMock()
    return mock


@pytest.fixture
def mock_refresh_token_repository():
    """Mock RefreshTokenRepository with common async methods."""
    mock = Mock()
    mock.create_from_jti = AsyncMock()
    mock.get_by_jti_hash = AsyncMock()
    mock.revoke = AsyncMock()
    mock.delete_expired = AsyncMock()
    return mock


@pytest.fixture
def mock_oauth_account_repository():
    """Mock OAuthAccountRepository with common async methods."""
    mock = Mock()
    mock.get_by_provider_user_id = AsyncMock()
    mock.create = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_password_reset_repository():
    """Mock PasswordResetRepository with common async methods."""
    mock = Mock()
    mock.create = AsyncMock()
    mock.get_valid = AsyncMock()
    mock.mark_used = AsyncMock()
    mock.delete_expired = AsyncMock()
    return mock


@pytest.fixture
def mock_wallet_repository():
    """Mock WalletRepository with common async methods."""
    mock = Mock()
    mock.create = AsyncMock()
    mock.get_by_address = AsyncMock()
    mock.list_by_user = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_portfolio_snapshot_repository():
    """Mock PortfolioSnapshotRepository with common async methods."""
    mock = Mock()
    mock.get_snapshots_in_range = AsyncMock()
    mock.get_by_wallet_address = AsyncMock()
    mock.create = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_historical_balance_repository():
    """Mock HistoricalBalanceRepository with common async methods."""
    mock = Mock()
    mock.create = AsyncMock()
    mock.get_by_wallet_and_token = AsyncMock()
    mock.list_by_wallet = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_token_repository():
    """Mock TokenRepository with common async methods."""
    mock = Mock()
    mock.create = AsyncMock()
    mock.get_by_address = AsyncMock()
    mock.list_all = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_token_price_repository():
    """Mock TokenPriceRepository with common async methods."""
    mock = Mock()
    mock.create = AsyncMock()
    mock.get_latest_by_token = AsyncMock()
    mock.list_by_token = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_token_balance_repository():
    """Mock TokenBalanceRepository with common async methods."""
    mock = Mock()
    mock.create = AsyncMock()
    mock.get_by_wallet_and_token = AsyncMock()
    mock.list_by_wallet = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


# === DI REPOSITORY FIXTURES (MOCKED) ===


@pytest.fixture
def user_repository_with_di(mock_database, mock_audit):
    """Create UserRepository with mocked dependencies."""
    from app.repositories.user_repository import UserRepository

    return UserRepository(mock_database, mock_audit)


@pytest.fixture
def wallet_repository_with_di(mock_database, mock_audit):
    """Create WalletRepository with mocked dependencies."""
    from app.repositories.wallet_repository import WalletRepository

    return WalletRepository(mock_database, mock_audit)


@pytest.fixture
def token_repository_with_di(mock_database, mock_audit):
    """Create TokenRepository with mocked dependencies."""
    from app.repositories.token_repository import TokenRepository

    return TokenRepository(mock_database, mock_audit)


@pytest.fixture
def token_price_repository_with_di(mock_database, mock_audit):
    """Create TokenPriceRepository with mocked dependencies."""
    from app.repositories.token_price_repository import TokenPriceRepository

    return TokenPriceRepository(mock_database, mock_audit)


@pytest.fixture
def email_verification_repository_with_di(mock_database, mock_audit):
    """Create EmailVerificationRepository with mocked dependencies."""
    from app.repositories.email_verification_repository import (
        EmailVerificationRepository,
    )

    return EmailVerificationRepository(mock_database, mock_audit)


@pytest.fixture
def oauth_account_repository_with_di(mock_database, mock_audit):
    """Create OAuthAccountRepository with mocked dependencies."""
    from app.repositories.oauth_account_repository import (
        OAuthAccountRepository,
    )

    return OAuthAccountRepository(mock_database, mock_audit)


@pytest.fixture
def password_reset_repository_with_di(mock_database, mock_audit):
    """Create PasswordResetRepository with mocked dependencies."""
    from app.repositories.password_reset_repository import (
        PasswordResetRepository,
    )

    return PasswordResetRepository(mock_database, mock_audit)


@pytest.fixture
def refresh_token_repository_with_di(mock_database, mock_audit):
    """Create RefreshTokenRepository with mocked dependencies."""
    from app.repositories.refresh_token_repository import (
        RefreshTokenRepository,
    )

    return RefreshTokenRepository(mock_database, mock_audit)


@pytest.fixture
def portfolio_snapshot_repository_with_di(mock_database, mock_audit):
    """Create PortfolioSnapshotRepository with mocked dependencies."""
    from app.repositories.portfolio_snapshot_repository import (
        PortfolioSnapshotRepository,
    )

    return PortfolioSnapshotRepository(mock_database, mock_audit)


@pytest.fixture
def historical_balance_repository_with_di(mock_database, mock_audit):
    """Create HistoricalBalanceRepository with mocked dependencies."""
    from app.repositories.historical_balance_repository import (
        HistoricalBalanceRepository,
    )

    return HistoricalBalanceRepository(mock_database, mock_audit)


@pytest.fixture
def token_balance_repository_with_di(mock_database, mock_audit):
    """Create TokenBalanceRepository with mocked dependencies."""
    from app.repositories.token_balance_repository import (
        TokenBalanceRepository,
    )

    return TokenBalanceRepository(mock_database, mock_audit)


# === DI REPOSITORY FIXTURES (REAL DATABASE) ===


def create_real_database(db_session):
    """Create a real database mock for testing that uses the provided session."""
    from unittest.mock import Mock
    
    mock_database = Mock()
    
    @asynccontextmanager
    async def mock_get_session():
        yield db_session
    
    mock_database.get_session = mock_get_session
    return mock_database


@pytest.fixture
def user_repository_with_real_db(db_session):
    """Create UserRepository with real database session for integration tests."""
    from app.repositories.user_repository import UserRepository
    from app.utils.logging import Audit

    database = create_real_database(db_session)
    audit = Audit()

    return UserRepository(database, audit)


@pytest.fixture
def wallet_repository_with_real_db(db_session):
    """Create WalletRepository with real database session for integration tests."""
    from app.repositories.wallet_repository import WalletRepository
    from app.utils.logging import Audit

    database = create_real_database(db_session)
    audit = Audit()

    return WalletRepository(database, audit)


@pytest.fixture
def token_repository_with_real_db(db_session):
    """Create TokenRepository with real database session for integration tests."""
    from app.repositories.token_repository import TokenRepository
    from app.utils.logging import Audit

    database = create_real_database(db_session)
    audit = Audit()

    return TokenRepository(database, audit)


@pytest.fixture
def token_price_repository_with_real_db(db_session):
    """Create TokenPriceRepository with real database session for integration tests."""
    from app.repositories.token_price_repository import TokenPriceRepository
    from app.utils.logging import Audit

    database = create_real_database(db_session)
    audit = Audit()

    return TokenPriceRepository(database, audit)


@pytest.fixture
def token_balance_repository_with_real_db(db_session):
    """Create TokenBalanceRepository with real database session for integration tests."""
    from app.repositories.token_balance_repository import (
        TokenBalanceRepository,
    )
    from app.utils.logging import Audit

    database = create_real_database(db_session)
    audit = Audit()

    return TokenBalanceRepository(database, audit)


@pytest.fixture
def historical_balance_repository_with_real_db(db_session):
    """Create HistoricalBalanceRepository with real database session for integration tests."""
    from app.repositories.historical_balance_repository import (
        HistoricalBalanceRepository,
    )
    from app.utils.logging import Audit

    database = create_real_database(db_session)
    audit = Audit()

    return HistoricalBalanceRepository(database, audit)


@pytest.fixture
def password_reset_repository_with_real_db(db_session):
    """Create PasswordResetRepository with real database session for integration tests."""
    from app.repositories.password_reset_repository import (
        PasswordResetRepository,
    )
    from app.utils.logging import Audit

    database = create_real_database(db_session)
    audit = Audit()

    return PasswordResetRepository(database, audit)


@pytest.fixture
def refresh_token_repository_with_real_db(db_session):
    """Create RefreshTokenRepository with real database session for integration tests."""
    from app.repositories.refresh_token_repository import (
        RefreshTokenRepository,
    )
    from app.utils.logging import Audit

    database = create_real_database(db_session)
    audit = Audit()

    return RefreshTokenRepository(database, audit)


@pytest.fixture
def email_verification_repository_with_real_db(db_session):
    """Create EmailVerificationRepository with real database session for integration tests."""
    from app.repositories.email_verification_repository import (
        EmailVerificationRepository,
    )
    from app.utils.logging import Audit

    database = create_real_database(db_session)
    audit = Audit()

    return EmailVerificationRepository(database, audit)
