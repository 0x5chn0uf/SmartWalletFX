import uuid
from decimal import Decimal

import pytest

from app.domain.schemas.token_price import TokenPriceCreate
from app.models import Token, TokenPrice


@pytest.mark.unit
def test_create_token_price_model():
    """Test creating a token price model directly (unit test without database)."""
    # Generate a UUID for the token_id
    token_uuid = uuid.uuid4()

    # Create a token price using the schema
    price_data = TokenPriceCreate(token_id=token_uuid, price_usd=123.45)
    token_price = TokenPrice(**price_data.model_dump())

    # Test that the model can be created
    assert token_price.token_id == token_uuid
    assert float(token_price.price_usd) == 123.45
    assert token_price.id is None  # Not saved yet

    # Test that the model has the expected attributes
    assert hasattr(token_price, "token_id")
    assert hasattr(token_price, "price_usd")
    assert hasattr(token_price, "id")
    assert hasattr(token_price, "timestamp")
    assert hasattr(token_price, "token")  # relationship


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_price_validation():
    """Test token price model validation."""
    # Test that we can create valid model
    valid_data = {"token_id": 1, "price_usd": Decimal("123.45")}
    token_price = TokenPrice(**valid_data)
    assert token_price.price_usd == Decimal("123.45")

    # Test that negative prices are allowed (for edge cases)
    negative_data = {"token_id": 1, "price_usd": Decimal("-10.0")}
    token_price_negative = TokenPrice(**negative_data)
    assert token_price_negative.price_usd == Decimal("-10.0")


# Add more tests for token price validation and edge cases here.
