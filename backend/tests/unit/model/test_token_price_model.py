import pytest

from app.models import Token, TokenPrice


def test_create_token_price(db_session):
    # Crée un token pour la FK
    token = Token(address="0x123", symbol="TKN", name="Token", decimals=18)
    db_session.add(token)
    db_session.commit()
    # Crée un prix de token
    price = TokenPrice(token_id=token.id, price_usd=123.45)
    db_session.add(price)
    db_session.commit()
    assert price.id is not None
    assert price.token_id == token.id
    assert float(price.price_usd) == pytest.approx(123.45)


# Add more tests for token price validation and edge cases here.
