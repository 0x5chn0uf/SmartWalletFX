import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.user import User
from app.schemas.portfolio_metrics import PortfolioMetrics
from app.schemas.portfolio_timeline import PortfolioTimeline
from app.schemas.wallet import WalletCreate
from app.usecase.wallet_usecase import WalletUsecase


def _dummy_user() -> SimpleNamespace:  # helper
    return SimpleNamespace(id=uuid.uuid4())


@pytest.mark.asyncio
async def test_create_wallet_success(db_session):
    data = WalletCreate(address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", name="UC")
    usecase = WalletUsecase(db_session, _dummy_user())
    wallet = await usecase.create_wallet(data)
    assert wallet.address == data.address
    assert wallet.name == "UC"


@pytest.mark.asyncio
async def test_create_wallet_duplicate(db_session):
    data = WalletCreate(address="0xabcdefabcdefabcdefabcdefabcdefabcdefabce")
    usecase = WalletUsecase(db_session, _dummy_user())
    await usecase.create_wallet(data)

    with pytest.raises(HTTPException) as exc:
        await usecase.create_wallet(data)

    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


@pytest.mark.asyncio
async def test_create_wallet_invalid_address(db_session):
    with pytest.raises(ValidationError):
        WalletCreate(address="notanaddress")


@pytest.mark.asyncio
async def test_list_wallets(db_session):
    usecase = WalletUsecase(db_session, _dummy_user())
    await usecase.create_wallet(
        WalletCreate(address="0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"),
    )
    await usecase.create_wallet(
        WalletCreate(address="0x2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b"),
    )
    wallets = await usecase.list_wallets()
    assert len(wallets) == 2


@pytest.mark.asyncio
async def test_delete_wallet_success(db_session):
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]
    usecase = WalletUsecase(db_session, _dummy_user())
    await usecase.create_wallet(WalletCreate(address=addr))
    await usecase.delete_wallet(addr)

    # Suppression d'un wallet inexistant
    with pytest.raises(HTTPException) as exc:
        await usecase.delete_wallet(addr)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_verify_wallet_ownership_owned_wallet(db_session):
    """Test wallet ownership verification for owned wallet."""
    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id)
    # Insert user row with unique username/email
    uname = f"testuser_{user_id.hex[:8]}"
    email = f"{uname}@example.com"
    db_user = User(id=user_id, username=uname, email=email)
    db_session.add(db_user)
    await db_session.commit()
    addr = f"0x{user_id.hex:0<40}"[:42]
    usecase = WalletUsecase(db_session, user)
    # Create wallet for the user
    await usecase.create_wallet(WalletCreate(address=addr))
    # Fetch wallet from DB and print user_id
    from app.models.wallet import Wallet as WalletModel

    result_wallet = await db_session.execute(
        WalletModel.__table__.select().where(WalletModel.address == addr)
    )
    row = result_wallet.fetchone()
    print(f"[DEBUG] Wallet row: {row}")
    # Verify ownership
    result = await usecase.verify_wallet_ownership(addr)
    assert result is True


@pytest.mark.asyncio
async def test_verify_wallet_ownership_not_owned(db_session):
    """Test wallet ownership verification for wallet not owned by user."""
    from app.models.user import User

    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    user1 = SimpleNamespace(id=user1_id)
    user2 = SimpleNamespace(id=user2_id)
    # Insert user rows with unique usernames/emails
    uname1 = f"user1_{user1_id.hex[:8]}"
    email1 = f"{uname1}@example.com"
    uname2 = f"user2_{user2_id.hex[:8]}"
    email2 = f"{uname2}@example.com"
    db_user1 = User(id=user1_id, username=uname1, email=email1)
    db_user2 = User(id=user2_id, username=uname2, email=email2)
    db_session.add_all([db_user1, db_user2])
    await db_session.commit()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]
    # Create wallet for user1
    usecase1 = WalletUsecase(db_session, user1)
    await usecase1.create_wallet(WalletCreate(address=addr))
    # Try to verify ownership with user2
    usecase2 = WalletUsecase(db_session, user2)
    result = await usecase2.verify_wallet_ownership(addr)
    assert result is False


@pytest.mark.asyncio
async def test_verify_wallet_ownership_nonexistent_wallet(db_session):
    """Test wallet ownership verification for nonexistent wallet."""
    from app.models.user import User

    user_id = uuid.uuid4()
    user = SimpleNamespace(id=user_id)
    # Insert user row with unique username/email
    uname = f"nouser_{user_id.hex[:8]}"
    email = f"{uname}@example.com"
    db_user = User(id=user_id, username=uname, email=email)
    db_session.add(db_user)
    await db_session.commit()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]
    usecase = WalletUsecase(db_session, user)
    result = await usecase.verify_wallet_ownership(addr)
    assert result is False


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_success(db_session):
    """Test successful portfolio snapshots retrieval."""
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]
    usecase = WalletUsecase(db_session, user)

    # Create wallet for the user
    await usecase.create_wallet(WalletCreate(address=addr))

    # Mock portfolio snapshot repository
    mock_snapshots = [
        {"timestamp": int(datetime.utcnow().timestamp()), "value": 1000.0},
        {
            "timestamp": int((datetime.utcnow() - timedelta(days=1)).timestamp()),
            "value": 950.0,
        },
    ]
    usecase.portfolio_snapshot_repository.get_snapshots_by_address_and_range = (
        AsyncMock(return_value=mock_snapshots)
    )

    result = await usecase.get_portfolio_snapshots(addr)
    assert result == mock_snapshots


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_not_owned(db_session):
    """Test portfolio snapshots retrieval for wallet not owned by user."""
    user1 = _dummy_user()
    user2 = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    # Create wallet for user1
    usecase1 = WalletUsecase(db_session, user1)
    await usecase1.create_wallet(WalletCreate(address=addr))

    # Try to get snapshots with user2
    usecase2 = WalletUsecase(db_session, user2)
    with pytest.raises(HTTPException) as exc:
        await usecase2.get_portfolio_snapshots(addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or you do not have permission" in exc.value.detail


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_nonexistent_wallet(db_session):
    """Test portfolio snapshots retrieval for nonexistent wallet."""
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]
    usecase = WalletUsecase(db_session, user)

    with pytest.raises(HTTPException) as exc:
        await usecase.get_portfolio_snapshots(addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or you do not have permission" in exc.value.detail


@pytest.mark.asyncio
async def test_get_portfolio_metrics_success(db_session):
    """Test successful portfolio metrics retrieval."""
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]
    usecase = WalletUsecase(db_session, user)

    # Create wallet for the user
    await usecase.create_wallet(WalletCreate(address=addr))

    # Mock portfolio calculation service
    mock_metrics = PortfolioMetrics(
        user_address=addr,
        total_collateral=1000.0,
        total_borrowings=200.0,
        total_collateral_usd=50000.0,
        total_borrowings_usd=10000.0,
        aggregate_health_score=0.85,
        aggregate_apy=0.08,
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        protocol_breakdown={},
        timestamp=datetime.utcnow(),
    )

    with patch(
        "app.services.portfolio_service.PortfolioCalculationService"
    ) as mock_service_class:
        mock_service = Mock()
        mock_service.calculate_portfolio_metrics = AsyncMock(return_value=mock_metrics)
        mock_service_class.return_value = mock_service

        result = await usecase.get_portfolio_metrics(addr)

        assert result == mock_metrics
        mock_service.calculate_portfolio_metrics.assert_called_once_with(
            user_address=addr
        )


@pytest.mark.asyncio
async def test_get_portfolio_metrics_not_owned(db_session):
    """Test portfolio metrics retrieval for wallet not owned by user."""
    user1 = _dummy_user()
    user2 = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    # Create wallet for user1
    usecase1 = WalletUsecase(db_session, user1)
    await usecase1.create_wallet(WalletCreate(address=addr))

    # Try to get metrics with user2
    usecase2 = WalletUsecase(db_session, user2)
    with pytest.raises(HTTPException) as exc:
        await usecase2.get_portfolio_metrics(addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or you do not have permission" in exc.value.detail


@pytest.mark.asyncio
async def test_get_portfolio_timeline_success(db_session):
    """Test successful portfolio timeline retrieval."""
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]
    usecase = WalletUsecase(db_session, user)

    # Create wallet for the user
    await usecase.create_wallet(WalletCreate(address=addr))

    # Mock portfolio calculation service
    mock_timeline = PortfolioTimeline(
        timestamps=[1234567890, 1234567891],
        collateral_usd=[50000.0, 51000.0],
        borrowings_usd=[10000.0, 10500.0],
    )

    with patch(
        "app.services.portfolio_service.PortfolioCalculationService"
    ) as mock_service_class:
        mock_service = Mock()
        mock_service.calculate_portfolio_timeline = AsyncMock(
            return_value=mock_timeline
        )
        mock_service_class.return_value = mock_service

        result = await usecase.get_portfolio_timeline(
            addr, interval="daily", limit=30, offset=0
        )

        assert result == mock_timeline
        mock_service.calculate_portfolio_timeline.assert_called_once_with(
            user_address=addr,
            interval="daily",
            limit=30,
            offset=0,
        )


@pytest.mark.asyncio
async def test_get_portfolio_timeline_not_owned(db_session):
    """Test portfolio timeline retrieval for wallet not owned by user."""
    user1 = _dummy_user()
    user2 = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]

    # Create wallet for user1
    usecase1 = WalletUsecase(db_session, user1)
    await usecase1.create_wallet(WalletCreate(address=addr))

    # Try to get timeline with user2
    usecase2 = WalletUsecase(db_session, user2)
    with pytest.raises(HTTPException) as exc:
        await usecase2.get_portfolio_timeline(addr)

    assert exc.value.status_code == 404
    assert "Wallet not found or you do not have permission" in exc.value.detail


@pytest.mark.asyncio
async def test_get_portfolio_timeline_with_custom_parameters(db_session):
    """Test portfolio timeline retrieval with custom parameters."""
    user = _dummy_user()
    addr = f"0x{uuid.uuid4().hex:0<40}"[:42]
    usecase = WalletUsecase(db_session, user)

    # Create wallet for the user
    await usecase.create_wallet(WalletCreate(address=addr))

    # Mock portfolio calculation service
    mock_timeline = PortfolioTimeline(
        timestamps=[1234567890],
        collateral_usd=[50000.0],
        borrowings_usd=[10000.0],
    )

    with patch(
        "app.services.portfolio_service.PortfolioCalculationService"
    ) as mock_service_class:
        mock_service = Mock()
        mock_service.calculate_portfolio_timeline = AsyncMock(
            return_value=mock_timeline
        )
        mock_service_class.return_value = mock_service

        result = await usecase.get_portfolio_timeline(
            addr, interval="weekly", limit=10, offset=5
        )

        assert result == mock_timeline
        mock_service.calculate_portfolio_timeline.assert_called_once_with(
            user_address=addr,
            interval="weekly",
            limit=10,
            offset=5,
        )
