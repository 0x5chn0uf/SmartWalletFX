from __future__ import annotations

from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.roles import UserRole
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService

TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword"
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "adminpassword"


async def create_user(
    db: AsyncSession, *, email: str, password: str, **kwargs: Any
) -> User:
    """Create a test user using the modern :class:`AuthService` API."""
    auth_service = AuthService(db)
    username: str = kwargs.get("username", email)
    payload = UserCreate(username=username, email=email, password=password)
    return await auth_service.register(payload)


async def create_admin_user(
    db: AsyncSession,
    *,
    email: str = TEST_ADMIN_EMAIL,
    password: str = TEST_ADMIN_PASSWORD,
    **kwargs: Any,
) -> User:
    """Create a test admin user."""
    auth_service = AuthService(db)
    username: str = kwargs.get("username", email)
    payload = UserCreate(username=username, email=email, password=password)
    user = await auth_service.register(payload)
    # Add admin role
    user.roles = [UserRole.ADMIN.value]
    await db.commit()
    await db.refresh(user)
    return user


async def create_authenticated_user(
    db: AsyncSession,
    client: AsyncClient,
    *,
    email: str = TEST_USER_EMAIL,
    password: str = TEST_USER_PASSWORD,
    is_admin: bool = False,
    **kwargs: Any,
) -> tuple[User, dict[str, str]]:
    """Create a user and return both user object and auth headers.

    Returns:
        Tuple of (user, auth_headers) for immediate use in tests.
    """
    if is_admin:
        user = await create_admin_user(db, email=email, password=password, **kwargs)
    else:
        user = await create_user(db, email=email, password=password, **kwargs)

    headers = await get_auth_headers(client, email, password)
    return user, headers


async def get_auth_headers(
    client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    """Authenticate and get authorization headers."""
    login_data = {"username": email, "password": password}
    response = await client.post("/auth/token", data=login_data)
    token_data = response.json()
    access_token = token_data["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


async def get_admin_headers(client: AsyncClient) -> dict[str, str]:
    """Get auth headers for admin user (creates if needed)."""
    return await get_auth_headers(client, TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)


async def create_test_users_batch(
    db: AsyncSession, count: int = 3, base_email: str = "testuser"
) -> list[User]:
    """Create multiple test users for batch testing scenarios."""
    users = []
    for i in range(count):
        email = f"{base_email}{i}@example.com"
        password = f"password{i}"
        user = await create_user(db, email=email, password=password)
        users.append(user)
    return users
