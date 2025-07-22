"""Authentication fixtures for the test suite."""

import uuid
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.user import UserCreate
from app.models import Wallet
from app.models.user import User
from app.usecase.auth_usecase import AuthUsecase


@pytest_asyncio.fixture
def auth_usecase(test_di_container_with_db):
    """Provides a fully configured AuthUsecase instance."""
    from app.main import ApplicationFactory

    # Ensure all dependencies are wired up by creating the app
    # which internally registers all components.
    app_factory = ApplicationFactory(test_di_container_with_db)
    app_factory.create_app()

    return test_di_container_with_db.get_usecase("auth")


@pytest_asyncio.fixture
async def get_auth_headers_for_user_factory(test_di_container_with_db):
    """Factory fixture to generate auth headers for a user."""
    from app.main import ApplicationFactory

    app_factory = ApplicationFactory(test_di_container_with_db)
    app_factory.create_app()
    jwt_utils = test_di_container_with_db.get_utility("jwt_utils")

    async def _get_auth_headers(user: User, roles: list = None) -> dict:
        """Generate authentication headers for a specific user with given roles."""
        # This is a simplified version. In a real app, you would log the user in.
        # For testing, we can directly create a token.

        token = jwt_utils.create_access_token(
            subject=str(user.id),
            additional_claims={"roles": roles or user.roles},
        )
        return {"Authorization": f"Bearer {token}"}

    return _get_auth_headers


@pytest_asyncio.fixture
async def get_auth_headers_for_role_factory(
    db_session: AsyncSession, get_auth_headers_for_user_factory, auth_usecase
):
    """Factory fixture to create a user with a role and get auth headers."""

    async def _get_auth_headers_for_role(role: str) -> dict:
        """Create a new user with a specific role and get auth headers."""
        # Create a new user for the role
        user_in = UserCreate(
            email=f"test.{role}.{uuid.uuid4()}@example.com",
            password="Str0ngPassword!",
            username=f"test.{role[:8]}.{str(uuid.uuid4())[:8]}",
        )

        user = await auth_usecase.register(user_in)
        user.email_verified = True
        user.roles = [role]
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        return await get_auth_headers_for_user_factory(user, roles=[role])

    return _get_auth_headers_for_role


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, auth_usecase: AuthUsecase):
    """
    Creates a new user in the database for testing.
    Returns the user without committing the session.
    """
    user_in = UserCreate(
        email=f"test.user.{uuid.uuid4()}@example.com",
        password="Str0ngPassword!",
        username=f"test.user.{uuid.uuid4()}",
    )
    user = await auth_usecase.register(user_in)
    # Mark as email verified for tests that require authentication
    user.email_verified = True
    db_session.add(user)
    # Don't commit here - let the test or other fixtures handle it
    return user


@pytest_asyncio.fixture
async def test_user_with_wallet(db_session: AsyncSession, auth_usecase):
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
    user = await auth_usecase.register(user_in)
    user.email_verified = True
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


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, auth_usecase):
    """
    Creates an admin user in the database for testing.
    Provides a test user with admin privileges.
    """
    user_in = UserCreate(
        email=f"admin.{uuid.uuid4()}@example.com",
        password="AdminPassword123!",
        username=f"admin.{uuid.uuid4()}",
    )
    user = await auth_usecase.register(user_in)
    user.email_verified = True
    user.roles = ["admin"]
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession, auth_usecase):
    """
    Creates an inactive user in the database for testing.
    Provides a test user that is not active.
    """
    user_in = UserCreate(
        email=f"inactive.{uuid.uuid4()}@example.com",
        password="InactivePassword123!",
        username=f"inactive.{uuid.uuid4()}",
    )
    user = await auth_usecase.register(user_in)
    user.email_verified = True
    user.is_active = False
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def authenticated_client(
    async_client: AsyncClient,
    test_user: User,
    auth_usecase: AuthUsecase,
    db_session: AsyncSession,
):
    """
    Returns an authenticated client for a given user.
    Creates auth token directly without authentication.
    """
    # Create token directly using JWT utils instead of authenticating
    jwt_utils = auth_usecase._AuthUsecase__jwt_utils
    token = jwt_utils.create_access_token(
        subject=str(test_user.id),
        additional_claims={"roles": test_user.roles},
    )

    async_client.headers = {
        "Authorization": f"Bearer {token}",
    }
    return async_client


@pytest_asyncio.fixture
def unverified_user_client(
    client: AsyncClient, unverified_user: User, auth_usecase: AuthUsecase
) -> AsyncClient:
    """Provides an authenticated client for an unverified user."""
    token_data = auth_usecase.create_access_token(user_id=unverified_user.id)
    client.headers = {
        "Authorization": f"Bearer {token_data.access_token}",
    }
    return client


@pytest_asyncio.fixture
async def create_user_and_wallet(db_session: AsyncSession, auth_usecase):
    """
    Provides a factory to create a user and a wallet.
    This allows creating multiple unique users within a single test.
    """

    async def _factory():
        # Create user
        user_in = UserCreate(
            email=f"factory.user.{uuid.uuid4()}@example.com",
            password="FactoryPassword123!",
            username=f"factory.user.{uuid.uuid4()}",
        )
        user = await auth_usecase.register(user_in)
        user.email_verified = True
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create wallet
        wallet = Wallet(
            user_id=user.id,
            address=f"0x{uuid.uuid4().hex}"[:42],
            name="Factory Wallet",
        )
        db_session.add(wallet)
        await db_session.commit()
        await db_session.refresh(wallet)

        return user, wallet

    return _factory


@pytest_asyncio.fixture
async def create_multiple_users(db_session: AsyncSession, auth_usecase):
    """
    Provides a factory to create multiple users.
    Useful for tests involving multiple user interactions.
    """

    async def _factory(count: int = 3):
        users = []
        for _ in range(count):
            user_in = UserCreate(
                email=f"multi.user.{uuid.uuid4()}@example.com",
                password="MultiUserPass123!",
                username=f"multi.user.{uuid.uuid4()}",
            )
            user = await auth_usecase.register(user_in)
            user.email_verified = True
            db_session.add(user)
            await db_session.commit()
            await db_session.refresh(user)
            users.append(user)
        return users

    return _factory


@pytest_asyncio.fixture
async def create_user_with_tokens(db_session: AsyncSession, auth_usecase):
    """
    Provides a factory to create a user with multiple wallets (tokens).
    Simulates a user holding different crypto assets.
    """

    async def _factory(wallet_count: int = 2):
        # Create user
        user_in = UserCreate(
            email=f"token.user.{uuid.uuid4()}@example.com",
            password="TokenUserPass123!",
            username=f"token.user.{uuid.uuid4()}",
        )
        user = await auth_usecase.register(user_in)
        user.email_verified = True
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create wallets
        wallets = []
        for i in range(wallet_count):
            wallet = Wallet(
                user_id=user.id,
                address=f"0x{uuid.uuid4().hex}"[:42],
                name=f"Token Wallet {i+1}",
            )
            db_session.add(wallet)
            await db_session.commit()
            await db_session.refresh(wallet)
            wallets.append(wallet)

        return user, wallets

    return _factory


@pytest_asyncio.fixture
async def mock_user_repo(db_session: AsyncSession):
    """Provides a mock UserRepository that interacts with the test database."""
    from app.repositories.user_repository import UserRepository

    mock_audit = Mock(spec="app.utils.logging.Audit")
    mock_db_service = Mock(spec="app.core.database.CoreDatabase")

    @asynccontextmanager
    async def get_session():
        yield db_session

    mock_db_service.get_session = get_session
    return UserRepository(mock_db_service, mock_audit)


@pytest_asyncio.fixture
async def mock_refresh_token_repo(db_session: AsyncSession):
    """
    Provides a mock RefreshTokenRepository for the test database.
    """
    from app.repositories.refresh_token_repository import (
        RefreshTokenRepository,
    )

    mock_audit = Mock(spec="app.utils.logging.Audit")
    mock_db_service = Mock(spec="app.core.database.CoreDatabase")

    @asynccontextmanager
    async def get_session():
        yield db_session

    mock_db_service.get_session = get_session
    return RefreshTokenRepository(mock_db_service, mock_audit)


def create_test_auth_usecase(db_session):
    """Return a fully wired AuthUsecase instance for unit/integration tests.

    This helper mirrors the *auth_usecase* fixture but can be imported
    directly inside tests (e.g. rate-limiter integration) without relying on
    fixture injection.  It initialises a minimal DI container backed by the
    provided *db_session* and returns the constructed :class:`AuthUsecase`.
    """
    # Wrap *db_session* inside a stub CoreDatabase that yields it via
    # get_session so that repositories operate on the same transactional
    # context without creating new engine connections.
    from contextlib import asynccontextmanager
    from unittest.mock import Mock

    from app.core.config import Configuration
    from app.core.database import CoreDatabase
    from app.repositories.email_verification_repository import (
        EmailVerificationRepository,
    )
    from app.repositories.refresh_token_repository import (
        RefreshTokenRepository,
    )
    from app.repositories.user_repository import UserRepository
    from app.services.email_service import EmailService
    from app.utils.jwt import JWTUtils
    from app.utils.logging import Audit

    database = Mock(spec=CoreDatabase)

    @asynccontextmanager
    async def get_session():
        yield db_session

    database.get_session = get_session

    audit = Audit()
    config = Configuration()
    jwt_utils = JWTUtils(config, audit)

    user_repo = UserRepository(database, audit)
    email_verification_repo = EmailVerificationRepository(database, audit)
    refresh_token_repo = RefreshTokenRepository(database, audit)
    email_service = EmailService(config, audit)

    return AuthUsecase(
        user_repository=user_repo,
        email_verification_repository=email_verification_repo,
        refresh_token_repository=refresh_token_repo,
        email_service=email_service,
        jwt_utils=jwt_utils,
        config=config,
        audit=audit,
    )
