import uuid

import httpx
import pytest

from app.domain.schemas.user import UserCreate


@pytest.mark.parametrize(
    "address_suffix",
    [
        "599",
        "598",
    ],
)
@pytest.mark.asyncio
async def test_create_token_balance_integration(
    test_app_with_di_container, test_di_container_with_db, address_suffix
):
    """Integration test for creating token balances with authentication."""
    # Get repositories and services from DIContainer
    user_repo = test_di_container_with_db.get_repository("user")
    auth_service = test_di_container_with_db.get_service("auth")
    jwt_utils = test_di_container_with_db.get_utility("jwt_utils")

    # Create user using DI pattern
    user_data = UserCreate(
        email=f"test.user.{uuid.uuid4()}@example.com",
        password="Str0ngPassword!",
        username=f"test.user.{uuid.uuid4()}",
    )
    user = await auth_service.register(user_data)
    user.email_verified = True
    await user_repo.save(user)

    # Create authenticated client for our user
    access_token = jwt_utils.create_access_token(
        subject=str(user.id),
        additional_claims={
            "email": user.email,
            "roles": getattr(user, "roles", ["individual_investor"]),
            "attributes": {},
        },
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    # Generate unique addresses to avoid conflicts between test runs
    unique_id = uuid.uuid4().hex[:8]
    # Ensure wallet address is exactly 42 characters (0x + 40 hex chars)
    wallet_address = f"0x{unique_id}{'0' * (40 - len(unique_id))}"
    # Make token address unique by including unique_id
    token_address = f"0x{unique_id}FAC5E5542a773Aa44fBCfeDf7C193bc2C{address_suffix}"

    wallet_data = {
        "address": wallet_address,
        "name": "Test Wallet",
    }
    token_data = {
        "address": token_address,
        "symbol": "WBTC",
        "name": "Wrapped Bitcoin",
        "decimals": 18,
    }

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as authenticated_client:
        # Create wallet using authenticated client
        resp = await authenticated_client.post("/wallets", json=wallet_data)
        assert resp.status_code == 201
        wallet = resp.json()

        # Create token using authenticated client
        resp = await authenticated_client.post("/tokens", json=token_data)
        assert resp.status_code == 201
        token = resp.json()

        # Create token balance using authenticated client
        balance_data = {
            "token_id": token["id"],
            "wallet_id": wallet["id"],
            "balance": 1.23,
            "balance_usd": 20000.00,
        }
        resp = await authenticated_client.post("/token_balances", json=balance_data)
        assert resp.status_code == 201
        balance = resp.json()

        # Verify the created balance
        assert balance["id"] is not None
        assert float(balance["balance"]) == pytest.approx(1.23)
        assert float(balance["balance_usd"]) == 20000.00


@pytest.mark.asyncio
async def test_create_token_balance_unauthorized(test_app_with_di_container):
    """Test that creating token balances without authentication fails."""
    unique_id = uuid.uuid4().hex[:8]
    # Ensure wallet address is exactly 42 characters (0x + 40 hex chars)
    wallet_address = f"0x{unique_id}{'0' * (40 - len(unique_id))}"

    wallet_data = {
        "address": wallet_address,
        "name": "Test Wallet",
    }
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as ac:
        # Try to create wallet without authentication
        resp = await ac.post("/wallets", json=wallet_data)
        assert resp.status_code == 401  # Should be unauthorized
