import uuid

import httpx
import pytest

from app.domain.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_returns_200(
    test_app_with_di_container,
    test_di_container_with_db,
):
    """
    Given an authenticated user and a wallet they own,
    When they request portfolio snapshots for that wallet,
    Then the response should be successful (200 OK).
    """
    # Get repositories and services from DIContainer
    user_repo = test_di_container_with_db.get_repository("user")
    wallet_repo = test_di_container_with_db.get_repository("wallet")
    auth_usecase = test_di_container_with_db.get_usecase("auth")
    jwt_utils = test_di_container_with_db.get_utility("jwt_utils")

    # Create user using DI pattern
    user_data = UserCreate(
        email=f"test.user.{uuid.uuid4()}@example.com",
        password="Str0ngPassword!",
        username=f"test.user.{uuid.uuid4()}",
    )
    user = await auth_usecase.register(user_data)
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

    # Create wallet using the DIContainer repository
    wallet = await wallet_repo.create(
        user_id=user.id,
        address=f"0x{uuid.uuid4().hex[:40]}",
        name="Test Wallet DI",
    )

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as client:
        response = await client.get(f"/wallets/{wallet.address}/portfolio/snapshots")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_for_nonexistent_wallet_returns_404(
    test_app_with_di_container,
    test_di_container_with_db,
):
    """Test 404 response for non-existent wallet."""
    # Get repositories and services from DIContainer
    user_repo = test_di_container_with_db.get_repository("user")
    auth_usecase = test_di_container_with_db.get_usecase("auth")
    jwt_utils = test_di_container_with_db.get_utility("jwt_utils")

    # Create user using DI pattern
    user_data = UserCreate(
        email=f"test.user.{uuid.uuid4()}@example.com",
        password="Str0ngPassword!",
        username=f"test.user.{uuid.uuid4()}",
    )
    user = await auth_usecase.register(user_data)
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

    non_existent_address = "0xnotarealaddress"
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as client:
        response = await client.get(
            f"/wallets/{non_existent_address}/portfolio/snapshots"
        )
        assert response.status_code == 404
