from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.wallet import Wallet
from app.repositories.wallet_repository import WalletRepository


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._WalletRepository__database.get_session = mock_get_session


@pytest.fixture
def mock_database():
    """Mock CoreDatabase."""
    return Mock()


@pytest.fixture
def mock_audit():
    """Mock Audit service."""
    return Mock()


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def wallet_repository(mock_database, mock_audit):
    """Create WalletRepository with mocked dependencies."""
    return WalletRepository(mock_database, mock_audit)


def test_wallet_repository_constructor_dependencies():
    """Test that WalletRepository properly accepts dependencies in constructor."""
    # Arrange
    mock_database = Mock()
    mock_audit = Mock()

    # Act
    repository = WalletRepository(mock_database, mock_audit)

    # Assert
    assert repository._WalletRepository__database == mock_database
    assert repository._WalletRepository__audit == mock_audit


@pytest.mark.asyncio
async def test_get_by_address_found(wallet_repository, mock_session):
    """Test getting wallet by address when wallet exists."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)
    address = "0x1234567890123456789012345678901234567890"

    mock_wallet = Mock()
    mock_wallet.address = address
    mock_wallet.id = uuid.uuid4()

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.first.return_value = mock_wallet
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    with patch("time.time", return_value=1000.0):
        result = await wallet_repository.get_by_address(address)

    # Assert
    assert result == mock_wallet
    mock_session.execute.assert_called_once()
    wallet_repository._WalletRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_address_not_found(wallet_repository, mock_session):
    """Test getting wallet by address when wallet doesn't exist."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)
    address = "0x1234567890123456789012345678901234567890"

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    with patch("time.time", return_value=1000.0):
        result = await wallet_repository.get_by_address(address)

    # Assert
    assert result is None
    mock_session.execute.assert_called_once()
    wallet_repository._WalletRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_get_by_address_exception_handling(wallet_repository, mock_session):
    """Test exception handling in get_by_address method."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    address = "0x1234567890123456789012345678901234567890"

    # Act & Assert
    with patch("time.time", return_value=1000.0):
        with pytest.raises(Exception, match="Database error"):
            await wallet_repository.get_by_address(address)

    wallet_repository._WalletRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_create_success(wallet_repository, mock_session):
    """Test successful creation of wallet."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)

    address = "0x1234567890123456789012345678901234567890"
    user_id = uuid.uuid4()
    name = "Test Wallet"

    # Create a mock wallet that will be returned after creation
    mock_wallet = Mock()
    mock_wallet.id = uuid.uuid4()
    mock_wallet.address = address
    mock_wallet.user_id = user_id
    mock_wallet.name = name
    mock_wallet.balance_usd = 0.0

    # Mock the refresh to update the wallet object
    async def mock_refresh(wallet):
        wallet.id = mock_wallet.id

    mock_session.refresh = AsyncMock(side_effect=mock_refresh)

    # Act
    with patch("time.time", return_value=1000.0):
        result = await wallet_repository.create(address, user_id, name)

    # Assert
    assert isinstance(result, Wallet)
    assert result.address == address
    assert result.user_id == user_id
    assert result.name == name
    assert result.balance_usd == 0.0
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    wallet_repository._WalletRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_create_with_default_name(wallet_repository, mock_session):
    """Test wallet creation with default name when no name provided."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)

    address = "0x1234567890123456789012345678901234567890"
    user_id = uuid.uuid4()

    # Mock the refresh to update the wallet object
    async def mock_refresh(wallet):
        wallet.id = uuid.uuid4()

    mock_session.refresh = AsyncMock(side_effect=mock_refresh)

    # Act
    with patch("time.time", return_value=1000.0):
        result = await wallet_repository.create(address, user_id)

    # Assert
    assert isinstance(result, Wallet)
    assert result.address == address
    assert result.user_id == user_id
    assert result.name == "Unnamed Wallet"
    assert result.balance_usd == 0.0
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    wallet_repository._WalletRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_create_duplicate_address(wallet_repository, mock_session):
    """Test wallet creation with duplicate address raises HTTPException."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)
    mock_session.commit.side_effect = IntegrityError("duplicate", None, None)

    address = "0x1234567890123456789012345678901234567890"
    user_id = uuid.uuid4()

    # Act & Assert
    with patch("time.time", return_value=1000.0):
        with pytest.raises(HTTPException) as exc_info:
            await wallet_repository.create(address, user_id)

    assert exc_info.value.status_code == 400
    assert "Wallet address already exists" in str(exc_info.value.detail)
    mock_session.rollback.assert_called_once()
    wallet_repository._WalletRepository__audit.warning.assert_called()


@pytest.mark.asyncio
async def test_create_general_exception_handling(wallet_repository, mock_session):
    """Test general exception handling in create method."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)
    mock_session.add.side_effect = Exception("Database error")

    address = "0x1234567890123456789012345678901234567890"
    user_id = uuid.uuid4()

    # Act & Assert
    with patch("time.time", return_value=1000.0):
        with pytest.raises(Exception, match="Database error"):
            await wallet_repository.create(address, user_id)

    wallet_repository._WalletRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_list_by_user_success(wallet_repository, mock_session):
    """Test successful listing of wallets by user."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)
    user_id = uuid.uuid4()

    mock_wallet1 = Mock()
    mock_wallet1.user_id = user_id
    mock_wallet1.address = "0x1234567890123456789012345678901234567890"
    mock_wallet2 = Mock()
    mock_wallet2.user_id = user_id
    mock_wallet2.address = "0x0987654321098765432109876543210987654321"

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = [mock_wallet1, mock_wallet2]
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    with patch("time.time", return_value=1000.0):
        result = await wallet_repository.list_by_user(user_id)

    # Assert
    assert result == [mock_wallet1, mock_wallet2]
    mock_session.execute.assert_called_once()
    wallet_repository._WalletRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_list_by_user_empty_result(wallet_repository, mock_session):
    """Test listing wallets by user when user has no wallets."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)
    user_id = uuid.uuid4()

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    with patch("time.time", return_value=1000.0):
        result = await wallet_repository.list_by_user(user_id)

    # Assert
    assert result == []
    mock_session.execute.assert_called_once()
    wallet_repository._WalletRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_list_by_user_exception_handling(wallet_repository, mock_session):
    """Test exception handling in list_by_user method."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    user_id = uuid.uuid4()

    # Act & Assert
    with patch("time.time", return_value=1000.0):
        with pytest.raises(Exception, match="Database error"):
            await wallet_repository.list_by_user(user_id)

    wallet_repository._WalletRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_delete_success(wallet_repository, mock_session):
    """Test successful deletion of wallet."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)

    address = "0x1234567890123456789012345678901234567890"
    user_id = uuid.uuid4()

    mock_wallet = Mock()
    mock_wallet.address = address
    mock_wallet.user_id = user_id

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.first.return_value = mock_wallet
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    with patch("time.time", return_value=1000.0):
        result = await wallet_repository.delete(address, user_id)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.delete.assert_called_once_with(mock_wallet)
    mock_session.commit.assert_called_once()
    wallet_repository._WalletRepository__audit.info.assert_called()


@pytest.mark.asyncio
async def test_delete_wallet_not_found(wallet_repository, mock_session):
    """Test deletion when wallet doesn't exist."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)

    address = "0x1234567890123456789012345678901234567890"
    user_id = uuid.uuid4()

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act & Assert
    with patch("time.time", return_value=1000.0):
        with pytest.raises(HTTPException) as exc_info:
            await wallet_repository.delete(address, user_id)

    assert exc_info.value.status_code == 404
    assert "Wallet not found" in str(exc_info.value.detail)
    wallet_repository._WalletRepository__audit.warning.assert_called()


@pytest.mark.asyncio
async def test_delete_unauthorized_user(wallet_repository, mock_session):
    """Test deletion when user is not the owner."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)

    address = "0x1234567890123456789012345678901234567890"
    user_id = uuid.uuid4()
    different_user_id = uuid.uuid4()

    mock_wallet = Mock()
    mock_wallet.address = address
    mock_wallet.user_id = different_user_id  # Different user owns the wallet

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.first.return_value = mock_wallet
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act & Assert
    with patch("time.time", return_value=1000.0):
        with pytest.raises(HTTPException) as exc_info:
            await wallet_repository.delete(address, user_id)

    assert exc_info.value.status_code == 404
    assert "Wallet not found" in str(exc_info.value.detail)
    wallet_repository._WalletRepository__audit.warning.assert_called()


@pytest.mark.asyncio
async def test_delete_general_exception_handling(wallet_repository, mock_session):
    """Test general exception handling in delete method."""
    # Arrange
    setup_mock_session(wallet_repository, mock_session)
    mock_session.execute.side_effect = Exception("Database error")

    address = "0x1234567890123456789012345678901234567890"
    user_id = uuid.uuid4()

    # Act & Assert
    with patch("time.time", return_value=1000.0):
        with pytest.raises(Exception, match="Database error"):
            await wallet_repository.delete(address, user_id)

    wallet_repository._WalletRepository__audit.error.assert_called_once()


@pytest.mark.asyncio
async def test_timing_measurements():
    """Test that timing measurements are properly calculated."""
    # Arrange
    mock_database = Mock()
    mock_audit = Mock()
    repository = WalletRepository(mock_database, mock_audit)

    mock_session = AsyncMock()
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    setup_mock_session(repository, mock_session)

    address = "0x1234567890123456789012345678901234567890"

    # Act
    with patch("time.time", side_effect=[1000.0, 1000.5]):  # 500ms duration
        await repository.get_by_address(address)

    # Assert
    audit_calls = mock_audit.info.call_args_list
    success_call = audit_calls[-1]  # Last call should be success
    call_args = success_call[1]  # Get keyword arguments
    assert call_args["duration_ms"] == 500


@pytest.mark.asyncio
async def test_audit_logging_patterns():
    """Test that audit logging follows consistent patterns."""
    # Arrange
    mock_database = Mock()
    mock_audit = Mock()
    repository = WalletRepository(mock_database, mock_audit)

    mock_session = AsyncMock()
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    setup_mock_session(repository, mock_session)

    address = "0x1234567890123456789012345678901234567890"

    # Act
    with patch("time.time", return_value=1000.0):
        await repository.get_by_address(address)

    # Assert
    audit_calls = mock_audit.info.call_args_list
    assert len(audit_calls) == 2  # started and success

    started_call = audit_calls[0]
    success_call = audit_calls[1]

    assert "wallet_repository_get_by_address_started" in str(started_call)
    assert "wallet_repository_get_by_address_success" in str(success_call)

    # Check that both calls include the address
    assert address in str(started_call)
    assert address in str(success_call)
