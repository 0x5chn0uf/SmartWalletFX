import uuid

import httpx
import pytest

from app.domain.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_portfolio_timeline_unauthorized(
    test_app_with_di_container, test_di_container_with_db
):
    """Accessing timeline without auth should return 401."""
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

    # Create wallet with authenticated client
    unique_hex = uuid.uuid4().hex
    addr = "0x" + unique_hex + "d" * (40 - len(unique_hex))

    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as authenticated_client:
        resp = await authenticated_client.post(
            "/wallets", json={"address": addr, "name": "Timeline"}
        )
        assert resp.status_code == 201

    # Unauthenticated request
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test"
    ) as ac:
        r = await ac.get(f"/wallets/{addr}/portfolio/timeline")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_portfolio_timeline_wrong_user(
    test_app_with_di_container, test_di_container_with_db
):
    """User B cannot access User A's timeline."""
    # Get repositories and services from DIContainer
    user_repo = test_di_container_with_db.get_repository("user")
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

    # User A creates a wallet
    unique_hex = uuid.uuid4().hex
    addr = "0x" + unique_hex + "d" * (40 - len(unique_hex))
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers_a
    ) as authenticated_client_a:
        resp = await authenticated_client_a.post(
            "/wallets", json={"address": addr, "name": "A Wallet"}
        )
        assert resp.status_code == 201

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

    # User B tries to access User A's timeline
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers_b
    ) as ac_b:
        resp_b = await ac_b.get(f"/wallets/{addr}/portfolio/timeline")
    assert resp_b.status_code == 404


@pytest.mark.asyncio
async def test_portfolio_timeline_wallet_not_found(
    test_app_with_di_container, test_di_container_with_db
):
    """Requesting timeline for non-existing wallet returns 404."""
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

    non_existing = "0x" + uuid.uuid4().hex + "d" * (40 - len(uuid.uuid4().hex))
    async with httpx.AsyncClient(
        app=test_app_with_di_container, base_url="http://test", headers=headers
    ) as authenticated_client:
        r = await authenticated_client.get(
            f"/wallets/{non_existing}/portfolio/timeline"
        )
    assert r.status_code == 404
