import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.domain.schemas.wallet import WalletCreate, WalletResponse
from app.usecase.wallet_usecase import WalletUsecase


def _dummy_user() -> SimpleNamespace:  # helper
    return SimpleNamespace(id=uuid.uuid4())


@pytest.fixture
def mock_wallet_repository():
    """Mock WalletRepository."""
    mock_repo = Mock()
    # Ensure async methods return AsyncMock
    mock_repo.create = AsyncMock()
    mock_repo.list_by_user = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.delete = AsyncMock()
    return mock_repo


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository."""
    mock_repo = Mock()
    # Make async methods return AsyncMock
    mock_repo.get_by_id = AsyncMock()
    return mock_repo


@pytest.fixture
def mock_portfolio_snapshot_repository():
    """Mock PortfolioSnapshotRepository."""
    mock_repo = Mock()
    # Make async methods return AsyncMock
    mock_repo.get_snapshots_by_address_and_range = AsyncMock()
    return mock_repo


@pytest.fixture
def mock_config():
    """Mock ConfigurationService."""
    return Mock()


@pytest.fixture
def mock_audit():
    """Mock Audit service."""
    return Mock()


@pytest.fixture
def wallet_usecase(
    mock_wallet_repository,
    mock_user_repository,
    mock_portfolio_snapshot_repository,
    mock_config,
    mock_audit,
):
    """Create WalletUsecase with mocked dependencies."""
    return WalletUsecase(
        wallet_repo=mock_wallet_repository,
        user_repo=mock_user_repository,
        portfolio_snapshot_repo=mock_portfolio_snapshot_repository,
        config_service=mock_config,
        audit=mock_audit,
    )


@pytest.mark.asyncio
async def test_create_wallet_success(wallet_usecase, mock_wallet_repository):
    """Test successful wallet creation."""
    # Arrange
    user = _dummy_user()
    data = WalletCreate(address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", name="UC")
    expected_wallet = WalletResponse(
        id=uuid.uuid4(),
        address=data.address,
        name=data.name,
        user_id=user.id,
        is_active=True,
        balance_usd=0.0,
    )

    mock_wallet_repository.create.return_value = expected_wallet

    # Act
    wallet = await wallet_usecase.create_wallet(user, data)

    # Assert
    assert wallet.address == data.address
    assert wallet.name == "UC"
    mock_wallet_repository.create.assert_called_once_with(
        address=data.address, user_id=user.id, name=data.name
    )


@pytest.mark.asyncio
async def test_create_wallet_duplicate(wallet_usecase, mock_wallet_repository):
    """Test wallet creation with duplicate address."""
    # Arrange
    user = _dummy_user()
    data = WalletCreate(address="0xabcdefabcdefabcdefabcdefabcdefabcdefabce")

    # Mock repository to raise HTTPException for duplicate
    mock_wallet_repository.create.side_effect = HTTPException(
        status_code=400, detail="Wallet already exists"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.create_wallet(user, data)

    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


@pytest.mark.asyncio
async def test_create_wallet_invalid_address():
    """Test wallet creation with invalid address."""
    with pytest.raises(ValidationError):
        WalletCreate(address="notanaddress")


@pytest.mark.asyncio
async def test_list_wallets(wallet_usecase, mock_wallet_repository):
    """Test listing wallets."""
    # Arrange
    user = _dummy_user()
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
    wallets = await wallet_usecase.list_wallets(user)

    # Assert
    assert len(wallets) == 2
    mock_wallet_repository.list_by_user.assert_called_once_with(user.id)


@pytest.mark.asyncio
async def test_delete_wallet_success(wallet_usecase, mock_wallet_repository):
    """Test successful wallet deletion."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.delete.return_value = True

    # Act
    await wallet_usecase.delete_wallet(user, addr)

    # Assert
    mock_wallet_repository.delete.assert_called_once_with(addr, user_id=user.id)


@pytest.mark.asyncio
async def test_delete_wallet_not_found(wallet_usecase, mock_wallet_repository):
    """Test wallet deletion when wallet not found."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.delete.side_effect = HTTPException(
        status_code=404, detail="Wallet not found"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.delete_wallet(user, addr)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_verify_wallet_ownership_owned_wallet(
    wallet_usecase, mock_wallet_repository
):
    """Test wallet ownership verification for owned wallet."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address_and_user.return_value = (
        Mock()
    )  # Wallet exists

    # Act
    result = await wallet_usecase.verify_wallet_ownership(user, addr)

    # Assert
    assert result is True
    mock_wallet_repository.get_by_address_and_user.assert_called_once_with(
        addr, user.id
    )


@pytest.mark.asyncio
async def test_verify_wallet_ownership_not_owned(
    wallet_usecase, mock_wallet_repository
):
    """Test wallet ownership verification for wallet not owned by user."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address_and_user.return_value = (
        None  # Wallet not found
    )

    # Act
    result = await wallet_usecase.verify_wallet_ownership(user, addr)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_verify_wallet_ownership_nonexistent_wallet(
    wallet_usecase, mock_wallet_repository
):
    """Test wallet ownership verification for nonexistent wallet."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address_and_user.return_value = None

    # Act
    result = await wallet_usecase.verify_wallet_ownership(user, addr)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_success(
    wallet_usecase, mock_wallet_repository, mock_portfolio_snapshot_repository
):
    """Test successful portfolio snapshots retrieval."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address_and_user.return_value = (
        Mock()
    )  # Wallet exists

    mock_snapshots = [
        {"timestamp": int(datetime.utcnow().timestamp()), "value": 1000.0},
        {
            "timestamp": int((datetime.utcnow() - timedelta(days=1)).timestamp()),
            "value": 950.0,
        },
    ]
    mock_portfolio_snapshot_repository.get_snapshots_by_address_and_range.return_value = (
        mock_snapshots
    )

    # Act
    result = await wallet_usecase.get_portfolio_snapshots(user, addr)

    # Assert
    assert result == mock_snapshots
    mock_wallet_repository.get_by_address_and_user.assert_called_once_with(
        addr, user.id
    )


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_not_owned(
    wallet_usecase, mock_wallet_repository
):
    """Test portfolio snapshots retrieval for wallet not owned by user."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address_and_user.return_value = (
        None  # Wallet not owned
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.get_portfolio_snapshots(user, addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or you do not have permission" in exc.value.detail


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_nonexistent_wallet(
    wallet_usecase, mock_wallet_repository
):
    """Test portfolio snapshots retrieval for nonexistent wallet."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address_and_user.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.get_portfolio_snapshots(user, addr)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_portfolio_metrics_not_owned(wallet_usecase, mock_wallet_repository):
    """Test portfolio metrics retrieval for wallet not owned by user."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address_and_user.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.get_portfolio_metrics(user, addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or you do not have permission" in exc.value.detail


@pytest.mark.asyncio
async def test_get_portfolio_timeline_not_owned(wallet_usecase, mock_wallet_repository):
    """Test portfolio timeline retrieval for wallet not owned by user."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address_and_user.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.get_portfolio_timeline(user, addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or you do not have permission" in exc.value.detail


def test_wallet_usecase_constructor_dependencies():
    """Test that WalletUsecase properly accepts dependencies in constructor."""
    # Arrange
    mock_wallet_repository = Mock()
    mock_user_repository = Mock()
    mock_portfolio_snapshot_repository = Mock()
    mock_config = Mock()
    mock_audit = Mock()

    # Act
    usecase = WalletUsecase(
        wallet_repo=mock_wallet_repository,
        user_repo=mock_user_repository,
        portfolio_snapshot_repo=mock_portfolio_snapshot_repository,
        config_service=mock_config,
        audit=mock_audit,
    )

    # Assert
    assert usecase._WalletUsecase__wallet_repo == mock_wallet_repository
    assert usecase._WalletUsecase__user_repo == mock_user_repository
    assert (
        usecase._WalletUsecase__portfolio_snapshot_repo
        == mock_portfolio_snapshot_repository
    )
    assert usecase._WalletUsecase__config_service == mock_config
    assert usecase._WalletUsecase__audit == mock_audit
