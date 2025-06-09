import pytest

from app.models import Token, TokenBalance, Wallet


def test_create_token_balance(db_session):
    # Crée un wallet et un token pour la FK
    wallet = Wallet(address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e", balance=0.0)
    token = Token(
        address="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        symbol="WBTC",
        name="Wrapped Bitcoin",
    )
    db_session.add_all([wallet, token])
    db_session.commit()
    # Crée un token balance
    balance = TokenBalance(
        wallet_id=wallet.id,
        token_id=token.id,
        balance=100000000,
        balance_usd=20000.00,
    )
    db_session.add(balance)
    db_session.commit()
    assert balance.id is not None
    assert balance.wallet_id == wallet.id
    assert balance.token_id == token.id
    assert float(balance.balance) == 100000000
    assert float(balance.balance_usd) == 20000.00


# Add more tests for balance validation and edge cases here.
