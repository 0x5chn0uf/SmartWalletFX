import pytest

from app.domain.errors import InactiveUserError, InvalidCredentialsError
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService

pytestmark = pytest.mark.anyio


async def test_authenticate_success(db_session):
    svc = AuthService(db_session)
    user_payload = UserCreate(
        username="alice",
        email="alice@example.com",
        password="Str0ng!pwd1@",
    )
    await svc.register(user_payload)

    tokens = await svc.authenticate("alice", "Str0ng!pwd1@")
    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"


async def test_authenticate_bad_password(db_session):
    svc = AuthService(db_session)
    user_payload = UserCreate(
        username="bob",
        email="bob@example.com",
        password="GoodP@ssw0rd",
    )
    await svc.register(user_payload)

    with pytest.raises(InvalidCredentialsError):
        await svc.authenticate("bob", "wrongpass")


async def test_authenticate_unknown_user(db_session):
    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentialsError):
        await svc.authenticate("nonexistent", "whatever")
