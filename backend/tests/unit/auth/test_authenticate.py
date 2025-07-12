import uuid

import pytest

from app.domain.errors import InvalidCredentialsError
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_authenticate_success(db_session):
    svc = AuthService(db_session)
    username = f"alice-{uuid.uuid4().hex[:8]}"
    email = f"alice-{uuid.uuid4().hex[:8]}@example.com"
    user_payload = UserCreate(
        username=username,
        email=email,
        password="Str0ng!pwd1@",
    )
    await svc.register(user_payload)

    # Verify the user's email directly in the database
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email(email)
    user.email_verified = True
    await db_session.commit()

    tokens = await svc.authenticate(username, "Str0ng!pwd1@")
    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"


@pytest.mark.asyncio
async def test_authenticate_bad_password(db_session):
    svc = AuthService(db_session)
    username = f"bob-{uuid.uuid4().hex[:8]}"
    email = f"bob-{uuid.uuid4().hex[:8]}@example.com"
    user_payload = UserCreate(
        username=username,
        email=email,
        password="GoodP@ssw0rd",
    )
    await svc.register(user_payload)

    # Verify the user's email directly in the database
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email(email)
    user.email_verified = True
    await db_session.commit()

    with pytest.raises(InvalidCredentialsError):
        await svc.authenticate("bob", "wrongpass")


@pytest.mark.asyncio
async def test_authenticate_unknown_user(db_session):
    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentialsError):
        await svc.authenticate("nonexistent", "whatever")
