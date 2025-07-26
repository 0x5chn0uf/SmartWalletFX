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
    mock_repo.get_by_address = AsyncMock()
    mock_repo.get_by_address_and_user = AsyncMock()
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
    mock_repo.get_by_wallet_address = AsyncMock()
    return mock_repo


@pytest.fixture
def mock_config():
    """Mock Configuration."""
    return Mock()


# Using shared fixtures from tests.shared.fixtures.core for mock_audit


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
        config=mock_config,
        audit=mock_audit,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_wallet_success(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
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
    mock_user_repository.get_by_id.return_value = user

    # Act
    wallet = await wallet_usecase.create_wallet(user.id, data)

    # Assert
    assert wallet.address == data.address
    assert wallet.name == "UC"
    mock_wallet_repository.create.assert_called_once_with(
        address=data.address, user_id=user.id, name=data.name
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_wallet_duplicate(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test wallet creation with duplicate address."""
    # Arrange
    user = _dummy_user()
    data = WalletCreate(address="0xabcdefabcdefabcdefabcdefabcdefabcdefabce")

    # Mock repository to raise HTTPException for duplicate
    mock_wallet_repository.create.side_effect = HTTPException(
        status_code=400, detail="Wallet already exists"
    )
    mock_user_repository.get_by_id.return_value = user

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.create_wallet(user.id, data)

    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_wallet_invalid_address():
    """Test wallet creation with invalid address."""
    with pytest.raises(ValidationError):
        WalletCreate(address="notanaddress")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_wallets(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
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
    mock_user_repository.get_by_id.return_value = user

    # Act
    wallets = await wallet_usecase.list_wallets(user.id)

    # Assert
    assert len(wallets) == 2
    mock_wallet_repository.list_by_user.assert_called_once_with(user.id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_wallet_success(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test successful wallet deletion."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.delete.return_value = True
    mock_user_repository.get_by_id.return_value = user

    # Act
    await wallet_usecase.delete_wallet(user.id, addr)

    # Assert
    mock_wallet_repository.delete.assert_called_once_with(addr, user_id=user.id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_wallet_not_found(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test wallet deletion when wallet not found."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.delete.side_effect = HTTPException(
        status_code=404, detail="Wallet not found"
    )
    mock_user_repository.get_by_id.return_value = user

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.delete_wallet(user.id, addr)

    assert exc.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_wallet_ownership_owned_wallet(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test wallet ownership verification for owned wallet."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    # Mock wallet exists and is owned by user
    mock_wallet = Mock()
    mock_wallet.user_id = user.id
    mock_wallet_repository.get_by_address.return_value = mock_wallet
    mock_user_repository.get_by_id.return_value = user

    # Act
    result = await wallet_usecase.verify_wallet_ownership(user.id, addr)

    # Assert
    assert result is True
    mock_wallet_repository.get_by_address.assert_called_once_with(address=addr)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_wallet_ownership_not_owned(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test wallet ownership verification for wallet not owned by user."""
    # Arrange
    user = _dummy_user()
    other_user_id = uuid.uuid4()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    # Mock wallet exists but is owned by different user
    mock_wallet = Mock()
    mock_wallet.user_id = other_user_id
    mock_wallet_repository.get_by_address.return_value = mock_wallet
    mock_user_repository.get_by_id.return_value = user

    # Act
    result = await wallet_usecase.verify_wallet_ownership(user.id, addr)

    # Assert
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_wallet_ownership_nonexistent_wallet(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test wallet ownership verification for nonexistent wallet."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address.return_value = None
    mock_user_repository.get_by_id.return_value = user

    # Act
    result = await wallet_usecase.verify_wallet_ownership(user.id, addr)

    # Assert
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_portfolio_snapshots_success(
    wallet_usecase,
    mock_wallet_repository,
    mock_portfolio_snapshot_repository,
    mock_user_repository,
):
    """Test successful portfolio snapshots retrieval."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    # Mock wallet exists and is owned by user (for verify_wallet_ownership)
    mock_wallet = Mock()
    mock_wallet.user_id = user.id
    mock_wallet_repository.get_by_address.return_value = mock_wallet
    mock_user_repository.get_by_id.return_value = user

    mock_snapshots = [
        {"timestamp": int(datetime.utcnow().timestamp()), "value": 1000.0},
        {
            "timestamp": int((datetime.utcnow() - timedelta(days=1)).timestamp()),
            "value": 950.0,
        },
    ]
    mock_portfolio_snapshot_repository.get_by_wallet_address.return_value = (
        mock_snapshots
    )

    # Act
    result = await wallet_usecase.get_portfolio_snapshots(user.id, addr)

    # Assert
    assert result == mock_snapshots
    mock_wallet_repository.get_by_address.assert_called_once_with(address=addr)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_portfolio_snapshots_not_owned(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test portfolio snapshots retrieval for wallet not owned by user."""
    # Arrange
    user = _dummy_user()
    other_user_id = uuid.uuid4()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    # Mock wallet exists but is owned by different user
    mock_wallet = Mock()
    mock_wallet.user_id = other_user_id
    mock_wallet_repository.get_by_address.return_value = mock_wallet
    mock_user_repository.get_by_id.return_value = user

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.get_portfolio_snapshots(user.id, addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or access denied" in exc.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_portfolio_snapshots_nonexistent_wallet(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test portfolio snapshots retrieval for nonexistent wallet."""
    # Arrange
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    mock_wallet_repository.get_by_address.return_value = None
    mock_user_repository.get_by_id.return_value = user

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.get_portfolio_snapshots(user.id, addr)

    assert exc.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_portfolio_metrics_not_owned(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test portfolio metrics retrieval for wallet not owned by user."""
    # Arrange
    user = _dummy_user()
    other_user_id = uuid.uuid4()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    # Mock wallet exists but is owned by different user
    mock_wallet = Mock()
    mock_wallet.user_id = other_user_id
    mock_wallet_repository.get_by_address.return_value = mock_wallet
    mock_user_repository.get_by_id.return_value = user

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.get_portfolio_metrics(user.id, addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or access denied" in exc.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_portfolio_timeline_not_owned(
    wallet_usecase, mock_wallet_repository, mock_user_repository
):
    """Test portfolio timeline retrieval for wallet not owned by user."""
    # Arrange
    user = _dummy_user()
    other_user_id = uuid.uuid4()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    # Mock wallet exists but is owned by different user
    mock_wallet = Mock()
    mock_wallet.user_id = other_user_id
    mock_wallet_repository.get_by_address.return_value = mock_wallet
    mock_user_repository.get_by_id.return_value = user

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await wallet_usecase.get_portfolio_timeline(user.id, addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or access denied" in exc.value.detail


import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.domain.schemas.wallet import WalletCreate, WalletResponse
from app.usecase.wallet_usecase import WalletUsecase


@pytest.fixture
def wallet_usecase_with_di(
    mock_wallet_repository,
    mock_user_repository,
    mock_portfolio_snapshot_repository,
    mock_config,
    mock_audit,
):
    """Provide WalletUsecase instance wired with the common mocked dependencies.
    This fixture mirrors the constructor-injection pattern used in the DI tests
    that were previously in *test_wallet_usecase_di.py*."""
    return WalletUsecase(
        wallet_repo=mock_wallet_repository,
        user_repo=mock_user_repository,
        portfolio_snapshot_repo=mock_portfolio_snapshot_repository,
        config=mock_config,
        audit=mock_audit,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_create_wallet_success_di(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Successful wallet creation using DI fixture (was _di module)."""
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_data = WalletCreate(address="0x" + "a" * 40, name="Test Wallet")
    expected_wallet = WalletResponse(
        id=uuid.uuid4(),
        address=wallet_data.address,
        name=wallet_data.name,
        user_id=user.id,
        is_active=True,
        balance_usd=0.0,
    )
    mock_wallet_repository.create.return_value = expected_wallet

    res = await wallet_usecase_with_di.create_wallet(user.id, wallet_data)

    assert res == expected_wallet
    mock_wallet_repository.create.assert_called_once_with(
        address=wallet_data.address, user_id=user.id, name=wallet_data.name
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wallet_usecase_create_wallet_duplicate_di(
    wallet_usecase_with_di, mock_wallet_repository
):
    """Duplicate wallet creation via DI raises HTTPException (was _di)."""
    user = SimpleNamespace(id=uuid.uuid4())
    wallet_data = WalletCreate(address="0x" + "b" * 40, name="Dup")

    mock_wallet_repository.create.side_effect = HTTPException(
        status_code=400, detail="Wallet already exists"
    )

    with pytest.raises(HTTPException) as exc:
        await wallet_usecase_with_di.create_wallet(user.id, wallet_data)

    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


import time
from datetime import datetime
from unittest.mock import patch

from fastapi import status

from app.domain.schemas.portfolio_metrics import PortfolioMetrics
from app.domain.schemas.portfolio_timeline import PortfolioTimeline


class TestWalletUsecaseEdgeCases:
    """Edge-case and error-handling scenarios merged from the former missing-coverage file."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_wallet_user_not_found(self, wallet_usecase_with_di):
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        wallet_create = WalletCreate(address="0x" + "c" * 40, name="Test")
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            await usecase.create_wallet(user_id, wallet_create)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_wallets_user_not_found(self, wallet_usecase_with_di):
        usecase = wallet_usecase_with_di
        user_id = uuid.uuid4()
        usecase._WalletUsecase__user_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(HTTPException):
            await usecase.list_wallets(user_id)


from datetime import datetime, timedelta

from app.domain.schemas.portfolio_metrics import PortfolioMetrics


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_portfolio_metrics_with_snapshot(
    wallet_usecase,
    mock_wallet_repository,
    mock_portfolio_snapshot_repository,
    mock_user_repository,
):
    """Metrics should be built from latest snapshot when available."""
    user = _dummy_user()
    mock_user_repository.get_by_id.return_value = user
    addr = "0x" + "d" * 40

    # snapshot list – most recent first
    now_ts = int(datetime.utcnow().timestamp())
    snapshot_dict = {
        "timestamp": now_ts,
        "total_collateral": 200.0,
        "total_borrowings": 80.0,
        "total_collateral_usd": 300.0,
        "total_borrowings_usd": 120.0,
        "aggregate_health_score": 0.95,
        "aggregate_apy": 7.5,
        "collaterals": [],
        "borrowings": [],
        "staked_positions": [],
        "health_scores": [],
        "protocol_breakdown": {},
    }
    mock_portfolio_snapshot_repository.get_by_wallet_address.return_value = [
        snapshot_dict
    ]
    # ownership check returns True
    mock_wallet_repository.get_by_address.return_value = SimpleNamespace(
        user_id=user.id
    )

    metrics: PortfolioMetrics = await wallet_usecase.get_portfolio_metrics(
        user.id, addr
    )

    assert metrics.total_collateral_usd == 300.0
    assert metrics.aggregate_health_score == 0.95
    mock_portfolio_snapshot_repository.get_by_wallet_address.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_portfolio_timeline_success(
    wallet_usecase,
    mock_wallet_repository,
    mock_portfolio_snapshot_repository,
    mock_user_repository,
):
    user = _dummy_user()
    mock_user_repository.get_by_id.return_value = user

    addr = "0x" + "e" * 40

    # Mock wallet ownership True
    mock_wallet_repository.get_by_address.return_value = SimpleNamespace(
        user_id=user.id
    )

    # timeline snapshots list
    base = datetime.utcnow()
    s1 = SimpleNamespace(
        timestamp=int(base.timestamp()),
        total_collateral_usd=100.0,
        total_borrowings_usd=50.0,
    )
    s2 = SimpleNamespace(
        timestamp=int((base - timedelta(days=1)).timestamp()),
        total_collateral_usd=None,
        total_borrowings_usd=None,
    )

    mock_portfolio_snapshot_repository.get_timeline = AsyncMock(return_value=[s1, s2])

    timeline = await wallet_usecase.get_portfolio_timeline(
        user.id, addr, "daily", 30, 0
    )

    assert timeline.timestamps == [
        int(base.timestamp()),
        int((base - timedelta(days=1)).timestamp()),
    ]
    assert timeline.collateral_usd == [100.0, 0.0]
    assert timeline.borrowings_usd == [50.0, 0.0]
    mock_portfolio_snapshot_repository.get_timeline.assert_awaited_once()
