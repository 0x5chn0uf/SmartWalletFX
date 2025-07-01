"""Authentication fixtures for the test suite."""

import uuid

import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Wallet
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.utils import security


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """
    Creates a new user in the database for testing.
    Provides a unique test user for each test function.
    """
    user_in = UserCreate(
        email=f"test.user.{uuid.uuid4()}@example.com",
        password="Str0ngPassword!",
        username=f"test.user.{uuid.uuid4()}",
    )
    user = await AuthService(db_session).register(user_in)
    return user


@pytest_asyncio.fixture
async def test_user_with_wallet(db_session: AsyncSession):
    """
    Creates a new user with a wallet in the database for testing.
    Provides a test user with an associated wallet.
    """
    # Create user
    user_in = UserCreate(
        email=f"test.user.{uuid.uuid4()}@example.com",
        password="Str0ngPassword!",
        username=f"test.user.{uuid.uuid4()}",
    )
    user = await AuthService(db_session).register(user_in)

    # Create wallet
    wallet = Wallet(
        user_id=user.id, address=f"0x{uuid.uuid4().hex}"[:42], name="Test Wallet"
    )
    db_session.add(wallet)
    await db_session.commit()
    await db_session.refresh(wallet)

    return user, wallet


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    """
    Creates an admin user in the database for testing.
    Provides a test user with admin privileges.
    """
    user_in = UserCreate(
        email=f"admin.{uuid.uuid4()}@example.com",
        password="AdminPassword123!",
        username=f"admin.{uuid.uuid4()}",
    )
    user = await AuthService(db_session).register(user_in)

    # Set admin role (assuming you have role management)
    user.is_admin = True
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession):
    """
    Creates an inactive user in the database for testing.
    Provides a test user that is not active.
    """
    user_in = UserCreate(
        email=f"inactive.{uuid.uuid4()}@example.com",
        password="InactivePassword123!",
        username=f"inactive.{uuid.uuid4()}",
    )
    user = await AuthService(db_session).register(user_in)

    # Set inactive status
    user.is_active = False
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def authenticated_client(db_session: AsyncSession, test_app, test_user: User):
    """
    Returns an authenticated client for a given user.
    Provides a fully configured async client with authentication.
    """
    from app.utils.jwt import JWTUtils

    async def _override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = _override_get_db

    access_token = JWTUtils.create_access_token(
        str(test_user.id),
        additional_claims={
            "email": test_user.email,
            "roles": ["individual_investor"],
            "attributes": {},
        },
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    async with AsyncClient(app=test_app, base_url="http://test", headers=headers) as ac:
        yield ac

    test_app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def admin_authenticated_client(
    db_session: AsyncSession, test_app, admin_user: User
):
    """
    Returns an authenticated client for an admin user.
    Provides a fully configured async client with admin authentication.
    """
    from app.utils.jwt import JWTUtils

    async def _override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = _override_get_db

    access_token = JWTUtils.create_access_token(
        str(admin_user.id),
        additional_claims={
            "email": admin_user.email,
            "roles": ["admin"],
            "attributes": {},
        },
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    async with AsyncClient(app=test_app, base_url="http://test", headers=headers) as ac:
        yield ac

    test_app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def create_user_and_wallet(db_session: AsyncSession):
    """Factory fixture to create a user and a wallet."""

    async def _factory():
        # Create user
        user = User(
            username=f"user-{uuid.uuid4()}",
            email=f"test.user.{uuid.uuid4()}@example.com",
            # Use the same test password across fixtures for consistency
            # Hash it using the application's PasswordHasher so that
            # AuthService.authenticate can successfully verify it.
            hashed_password=security.PasswordHasher.hash_password("S3cur3!pwd"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create wallet
        wallet = Wallet(
            user_id=user.id, address=f"0x{uuid.uuid4().hex}"[:42], name="Test Wallet"
        )
        db_session.add(wallet)
        await db_session.commit()
        await db_session.refresh(wallet)
        return user, wallet

    return _factory


@pytest_asyncio.fixture
async def create_multiple_users(db_session: AsyncSession):
    """Factory fixture to create multiple users for testing."""

    async def _factory(count: int = 3):
        users = []
        for i in range(count):
            user = User(
                username=f"user-{uuid.uuid4()}",
                email=f"test.user.{uuid.uuid4()}@example.com",
                hashed_password=security.PasswordHasher.hash_password("S3cur3!pwd"),
            )
            db_session.add(user)
            users.append(user)

        await db_session.commit()
        for user in users:
            await db_session.refresh(user)

        return users

    return _factory


@pytest_asyncio.fixture
async def create_user_with_tokens(db_session: AsyncSession):
    """Factory fixture to create a user with multiple wallets/tokens."""

    async def _factory(wallet_count: int = 2):
        # Create user
        user = User(
            username=f"user-{uuid.uuid4()}",
            email=f"test.user.{uuid.uuid4()}@example.com",
            hashed_password=security.PasswordHasher.hash_password("S3cur3!pwd"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create wallets
        wallets = []
        for i in range(wallet_count):
            wallet = Wallet(
                user_id=user.id,
                address=f"0x{uuid.uuid4().hex}"[:42],
                name=f"Test Wallet {i+1}",
            )
            db_session.add(wallet)
            wallets.append(wallet)

        await db_session.commit()
        for wallet in wallets:
            await db_session.refresh(wallet)

        return user, wallets

    return _factory
