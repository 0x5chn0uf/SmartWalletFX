import uuid
from datetime import datetime

import pytest
from sqlalchemy import event as _sa_event
from sqlalchemy.orm import Session

from app.repositories.historical_balance_repository import (
    HistoricalBalanceRepository,
)
from app.repositories.token_repository import TokenRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.historical_balance import HistoricalBalanceCreate
from app.schemas.token import TokenCreate
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_historical_balance_repository_create(db_session, monkeypatch):
    # First create a user using AuthService
    auth_service = AuthService(db_session)
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    password = "Str0ngP@ssw0rd!"
    user_create = UserCreate(username=username, email=email, password=password)
    user = await auth_service.register(user_create)

    # Create a wallet with the user's ID
    wallet_repo = WalletRepository(db_session)
    wallet = await wallet_repo.create(
        address="0x" + "1" * 40,  # Valid Ethereum address format (0x + 40 hex chars)
        name="Test Wallet",
        user_id=user.id,
    )

    token = await TokenRepository(db_session).create(
        TokenCreate(
            address=f"0x{uuid.uuid4().hex[:8] + '0' * 32}",  # Valid Ethereum address format
            symbol="HIS",
            name="Historical",
            decimals=18,
        )
    )

    hist = await HistoricalBalanceRepository(db_session).create(
        HistoricalBalanceCreate(
            wallet_id=wallet.id,
            token_id=token.id,
            balance=50.0,
            balance_usd=50.0,
            timestamp=datetime(2023, 1, 1, 12, 0, 0),  # Use a timezone-naive datetime
        )
    )
    assert hist.balance_usd == 50.0
