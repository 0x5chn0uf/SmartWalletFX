import time
import uuid

import httpx
import pytest

from app.domain.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_wallet_crud_authenticated(
    test_app_with_di_container, test_di_container_with_db
):
    """Authenticated user can create, list, and delete their wallet."""
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
    ) as authenticated_client:
        # First, check what wallets already exist
        resp = await authenticated_client.get("/wallets")
        assert resp.status_code == 200
        existing_addresses = [w["address"] for w in resp.json()]

        assert len(existing_addresses) == 0

        # Generate a truly unique address using timestamp
        timestamp = int(time.time() * 1000)  # milliseconds
        unique_hex = f"{timestamp:016x}"  # 16 hex chars
        wallet_address = "0x" + unique_hex + "d" * 24  # pad to 40 chars

        wallet_payload = {
            "address": wallet_address,
            "name": "My Wallet",
        }

        # Create
        resp = await authenticated_client.post("/wallets", json=wallet_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["address"] == wallet_payload["address"]
        assert data["name"] == wallet_payload["name"]
        assert data["user_id"] is not None

        # List should contain the wallet
        resp = await authenticated_client.get("/wallets")
        assert resp.status_code == 200
        wallets = resp.json()
        assert len(wallets) == 1
        assert wallets[0]["address"] == wallet_payload["address"]

        # Delete
        resp = await authenticated_client.delete(f"/wallets/{wallet_address}")
        assert resp.status_code == 204

        # List should be empty
        resp = await authenticated_client.get("/wallets")
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
async def test_wallet_crud_flow(test_app_with_di_container, test_di_container_with_db):
    """Create -> list -> delete wallet flow works via API."""
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

    # Generate unique address using proper hex
    unique_hex = uuid.uuid4().hex + uuid.uuid4().hex
    unique_address = "0x" + unique_hex[:40]  # Take first 40 hex chars

    payload = {"address": unique_address, "name": "Test Wallet"}

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as authenticated_client:
        # Create
        create_resp = await authenticated_client.post("/wallets", json=payload)
        assert create_resp.status_code == 201
        data = create_resp.json()
        assert data["address"].lower() == unique_address.lower()
        wallet_id = data["id"]

        # List should contain the wallet
        list_resp = await authenticated_client.get("/wallets")
        assert list_resp.status_code == 200
        wallets = list_resp.json()
        assert any(w["id"] == wallet_id for w in wallets)

        # Delete wallet
        del_resp = await authenticated_client.delete(f"/wallets/{unique_address}")
        assert del_resp.status_code == 204

        # List should now be empty
        list_resp2 = await authenticated_client.get("/wallets")
        assert list_resp2.status_code == 200
        assert list_resp2.json() == []


@pytest.mark.asyncio
async def test_wallet_duplicate_rejected(
    test_app_with_di_container, test_di_container_with_db
):
    """Creating the same wallet twice should yield 400."""
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

    # Generate unique address using proper hex
    unique_hex = uuid.uuid4().hex + uuid.uuid4().hex
    unique_address = "0x" + unique_hex[:40]  # Take first 40 hex chars

    payload = {"address": unique_address, "name": "Duplicate"}

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as authenticated_client:
        assert (
            await authenticated_client.post("/wallets", json=payload)
        ).status_code == 201
        dup = await authenticated_client.post("/wallets", json=payload)
        assert dup.status_code == 400
        assert "already exists" in dup.json()["detail"]


@pytest.mark.asyncio
async def test_wallet_invalid_address_format(
    test_app_with_di_container, test_di_container_with_db
):
    """API returns 422 for improperly formatted wallet address."""
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
    ) as authenticated_client:
        bad = await authenticated_client.post(
            "/wallets", json={"address": "not-an-address"}
        )
        assert bad.status_code == 422


@pytest.mark.asyncio
async def test_create_wallet_authenticated(
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

    wallet_data = {
        "address": "0x1234567890123456789012345678901234567890",
        "name": "Integration Wallet",
    }
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as authenticated_client:
        resp = await authenticated_client.post("/wallets", json=wallet_data)
        assert resp.status_code == 201
        json = resp.json()
        assert json["address"] == wallet_data["address"]
