import uuid

import httpx
import pytest

from app.domain.schemas.user import UserCreate

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_list_wallets_empty(
    test_app_with_di_container, test_di_container_with_db
):
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

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as client:
        response = await client.get("/wallets")
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
async def test_create_and_list_wallets(
    test_app_with_di_container, test_di_container_with_db
):
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

    addr = "0x" + "a" * 40
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as client:
        response = await client.post(
            "/wallets", json={"address": addr, "name": "Test Wallet"}
        )
        assert response.status_code == 201

        response = await client.get("/wallets")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["address"] == addr


@pytest.mark.asyncio
async def test_delete_wallet_success(
    test_app_with_di_container, test_di_container_with_db
):
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

    addr = "0x" + "b" * 40
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as client:
        response = await client.post(
            "/wallets",
            json={"address": addr, "name": "Wallet to Delete"},
        )
        assert response.status_code == 201

        response = await client.delete(f"/wallets/{addr}")
        assert response.status_code == 204

        response = await client.get("/wallets")
        assert response.status_code == 200
        assert not any(w["address"] == addr for w in response.json())


@pytest.mark.asyncio
async def test_delete_wallet_unauthorized(test_app_with_di_container):
    addr = "0x" + "c" * 40
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as client:
        response = await client.delete(f"/wallets/{addr}")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_wallet_wrong_user(
    test_app_with_di_container, test_di_container_with_db
):
    """A user cannot delete a wallet they don't own."""
    # Get repositories and services from DIContainer
    user_repo = test_di_container_with_db.get_repository("user")
    wallet_repo = test_di_container_with_db.get_repository("wallet")
    auth_usecase = test_di_container_with_db.get_usecase("auth")
    jwt_utils = test_di_container_with_db.get_utility("jwt_utils")

    # Create User A using DI pattern
    user_a_data = UserCreate(
        email=f"test.user.a.{uuid.uuid4()}@example.com",
        password="Str0ngPassword!",
        username=f"test.user.a.{uuid.uuid4()}",
    )
    user_a = await auth_usecase.register(user_a_data)
    user_a.email_verified = True
    await user_repo.save(user_a)

    # Create wallet for User A using DI
    wallet_a = await wallet_repo.create(
        user_id=user_a.id,
        address=f"0x{uuid.uuid4().hex[:40]}",
        name="User A Wallet",
    )

    # Create authenticated client for User A
    access_token_a = jwt_utils.create_access_token(
        subject=str(user_a.id),
        additional_claims={
            "email": user_a.email,
            "roles": getattr(user_a, "roles", ["individual_investor"]),
            "attributes": {},
        },
    )
    headers_a = {"Authorization": f"Bearer {access_token_a}"}

    # Verify User A can see their own wallet
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers_a
    ) as client_a:
        response = await client_a.get("/wallets")
        assert response.status_code == 200
        assert any(w["address"] == wallet_a.address for w in response.json())

    # Create User B using DI pattern
    user_b_data = UserCreate(
        email=f"test.user.b.{uuid.uuid4()}@example.com",
        password="Str0ngPassword!",
        username=f"test.user.b.{uuid.uuid4()}",
    )
    user_b = await auth_usecase.register(user_b_data)
    user_b.email_verified = True
    await user_repo.save(user_b)

    # Create authenticated client for User B
    access_token_b = jwt_utils.create_access_token(
        subject=str(user_b.id),
        additional_claims={
            "email": user_b.email,
            "roles": getattr(user_b, "roles", ["individual_investor"]),
            "attributes": {},
        },
    )
    headers_b = {"Authorization": f"Bearer {access_token_b}"}

    # User B tries to delete User A's wallet
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers_b
    ) as client_b:
        response = await client_b.delete(f"/wallets/{wallet_a.address}")
        assert response.status_code == 404
