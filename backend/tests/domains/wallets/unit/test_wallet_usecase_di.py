"""
Test WalletUsecase using new dependency injection pattern.

This demonstrates the new testing approach where usecases receive
their dependencies through constructor injection rather than direct
instantiation with session and user.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.domain.schemas.wallet import WalletCreate, WalletResponse
from app.usecase.wallet_usecase import WalletUsecase


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_create_wallet_success(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Test successful wallet creation with dependency injection."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_data = WalletCreate(
        address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", name="Test Wallet"
    )
    expected_wallet = WalletResponse(
        id=uuid.uuid4(),
        address=wallet_data.address,
        name=wallet_data.name,
        user_id=user.id,
        is_active=True,
        balance_usd=0.0,
    )

    mock_wallet_repository.create.return_value = expected_wallet

    # Act
    result = await wallet_usecase_with_di.create_wallet(user.id, wallet_data)

    # Assert
    assert result == expected_wallet
    mock_wallet_repository.create.assert_called_once_with(
        address=wallet_data.address, user_id=user.id, name=wallet_data.name
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_create_wallet_duplicate(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Test wallet creation with duplicate address raises HTTPException."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_data = WalletCreate(
        address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", name="Test Wallet"
    )

    # Mock repository to raise exception for duplicate
    mock_wallet_repository.create.side_effect = HTTPException(
        status_code=400, detail="Wallet already exists"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase_with_di.create_wallet(user, wallet_data)

    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_list_wallets(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Test listing wallets for a user."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    expected_wallets = [
        WalletResponse(
            id=uuid.uuid4(),
            address="0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a",
            name="Wallet 1",
            user_id=user.id,
            is_active=True,
            balance_usd=100.0,
        ),
        WalletResponse(
            id=uuid.uuid4(),
            address="0x2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b",
            name="Wallet 2",
            user_id=user.id,
            is_active=True,
            balance_usd=200.0,
        ),
    ]

    mock_wallet_repository.list_by_user.return_value = expected_wallets

    # Act
    result = await wallet_usecase_with_di.list_wallets(user.id)

    # Assert
    assert result == expected_wallets
    mock_wallet_repository.list_by_user.assert_called_once_with(user.id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_delete_wallet_success(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Test successful wallet deletion."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_address = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"

    # Act
    await wallet_usecase_with_di.delete_wallet(user.id, wallet_address)

    # Assert
    mock_wallet_repository.delete.assert_called_once_with(
        wallet_address, user_id=user.id
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_delete_wallet_not_found(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Test wallet deletion when wallet doesn't exist."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_address = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"

    # Mock repository to raise exception for non-existent wallet
    mock_wallet_repository.delete.side_effect = HTTPException(
        status_code=404, detail="Wallet not found"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase_with_di.delete_wallet(user, wallet_address)

    assert exc.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_verify_ownership_owned(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Test wallet ownership verification for owned wallet."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_address = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"

    # Mock wallet exists and belongs to user
    mock_wallet_repository.get_by_address.return_value = SimpleNamespace(
        address=wallet_address, user_id=user.id
    )

    # Act
    result = await wallet_usecase_with_di.verify_wallet_ownership(
        user.id, wallet_address
    )

    # Assert
    assert result is True
    mock_wallet_repository.get_by_address.assert_called_once_with(
        address=wallet_address
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_verify_ownership_not_owned(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Test wallet ownership verification for wallet not owned by user."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    other_user_id = uuid.uuid4()
    wallet_address = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"

    # Mock wallet exists but belongs to different user
    mock_wallet_repository.get_by_address.return_value = SimpleNamespace(
        address=wallet_address, user_id=other_user_id
    )

    # Act
    result = await wallet_usecase_with_di.verify_wallet_ownership(user, wallet_address)

    # Assert
    assert result is False
    mock_wallet_repository.get_by_address.assert_called_once_with(
        address=wallet_address
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_get_portfolio_snapshots(
    wallet_usecase_with_di, mock_wallet_repository, mock_portfolio_snapshot_repository
):
    """Test getting portfolio snapshots for a wallet."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_address = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
    expected_snapshots = [
        {"timestamp": 1234567890, "value": 1000.0},
        {"timestamp": 1234567891, "value": 1050.0},
    ]

    # Mock wallet ownership verification
    mock_wallet_repository.get_by_address.return_value = SimpleNamespace(
        address=wallet_address, user_id=user.id
    )

    # Mock portfolio snapshots
    mock_portfolio_snapshot_repository.get_by_wallet_address.return_value = (
        expected_snapshots
    )

    # Act
    result = await wallet_usecase_with_di.get_portfolio_snapshots(
        user.id, wallet_address
    )

    # Assert
    assert result == expected_snapshots
    mock_wallet_repository.get_by_address.assert_called_once_with(
        address=wallet_address
    )
    mock_portfolio_snapshot_repository.get_by_wallet_address.assert_called_once_with(
        wallet_address
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_get_portfolio_snapshots_not_owned(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Test getting portfolio snapshots for wallet not owned by user."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_address = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"

    # Mock wallet doesn't exist or not owned
    mock_wallet_repository.get_by_address.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase_with_di.get_portfolio_snapshots(user, wallet_address)

    assert exc.value.status_code == 404
    assert "not found or access denied" in exc.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_audit_logging(
    wallet_usecase_with_di, mock_wallet_repository, mock_audit
):
    """Test that audit logging is called appropriately."""
    # Arrange
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_data = WalletCreate(
        address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", name="Test Wallet"
    )

    mock_wallet_repository.create.return_value = WalletResponse(
        id=uuid.uuid4(),
        address=wallet_data.address,
        name=wallet_data.name,
        user_id=user.id,
        is_active=True,
        balance_usd=0.0,
    )

    # Act
    await wallet_usecase_with_di.create_wallet(user, wallet_data)

    # Assert audit logging was called
    mock_audit.info.assert_called()


@pytest.mark.unit
def test_wallet_usecase_constructor_dependencies():
    """Test that WalletUsecase properly accepts dependencies in constructor."""
    # Arrange
    mock_wallet_repository = Mock()
    mock_user_repository = Mock()  # Add missing user repository
    mock_portfolio_snapshot_repository = Mock()
    mock_config = Mock()
    mock_audit = Mock()

    # Act
    usecase = WalletUsecase(
        wallet_repo=mock_wallet_repository,
        user_repo=mock_user_repository,  # Add missing parameter
        portfolio_snapshot_repo=mock_portfolio_snapshot_repository,
        config=mock_config,
        audit=mock_audit,
    )

    # Assert
    assert usecase._WalletUsecase__wallet_repo == mock_wallet_repository
    assert usecase._WalletUsecase__user_repo == mock_user_repository  # Add assertion
    assert (
        usecase._WalletUsecase__portfolio_snapshot_repo
        == mock_portfolio_snapshot_repository
    )
    assert usecase._WalletUsecase__config_service == mock_config
    assert usecase._WalletUsecase__audit == mock_audit
