from datetime import datetime, timezone

import pytest

from app.models import HistoricalBalance, Token, Wallet


def test_create_historical_balance(db_session):
    # Crée un wallet et un token pour la FK
    wallet = Wallet(
        address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e", balance=0.0
    )
    token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
    )
    db_session.add_all([wallet, token])
    db_session.commit()
    # Crée un historique de balance
    timestamp = datetime.now(timezone.utc)
    hist_balance = HistoricalBalance(
        wallet_id=wallet.id,
        token_id=token.id,
        balance=100.0,
        balance_usd=20000.00,
        timestamp=timestamp,
    )
    db_session.add(hist_balance)
    db_session.commit()
    assert hist_balance.id is not None
    assert hist_balance.wallet_id == wallet.id
    assert hist_balance.token_id == token.id
    assert hist_balance.balance == 100.0
    assert hist_balance.timestamp.replace(tzinfo=timezone.utc) == timestamp
