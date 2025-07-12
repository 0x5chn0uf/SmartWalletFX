from typing import Dict

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.usefixtures("async_client_with_db")


async def _register_user(
    async_client: AsyncClient, username: str, email: str, password: str
) -> Dict[str, str]:
    """Register a user and return the response data."""
    res = await async_client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert res.status_code == 201
    return res.json()


@pytest.mark.asyncio
async def test_obtain_token_success(
    async_client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """Test successful token acquisition with valid credentials."""
    username = "dana"
    password = "Sup3rStr0ng!!"
    email = f"{username}@example.com"
    await _register_user(async_client_with_db, username, email, password)

    # Mark the user's email as verified directly in the database
    from app.repositories.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email(email)
    user.email_verified = True
    await db_session.commit()

    res = await async_client_with_db.post(
        "/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_obtain_token_bad_credentials(
    async_client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """Test token acquisition fails with invalid credentials."""
    username = "edgar"
    password = "GoodPwd1!!"
    email = f"{username}@example.com"
    await _register_user(async_client_with_db, username, email, password)

    # Mark the user's email as verified directly in the database
    from app.repositories.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email(email)
    user.email_verified = True
    await db_session.commit()

    res = await async_client_with_db.post(
        "/auth/token",
        data={"username": username, "password": "wrongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 401
