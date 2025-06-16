import pytest

from app.schemas.user import UserCreate
from app.services.auth_service import (
    AuthService,
    DuplicateError,
    WeakPasswordError,
)


@pytest.mark.anyio
async def test_register_success(db_session):
    service = AuthService(db_session)
    payload = UserCreate(
        username="alice", email="alice@example.com", password="Str0ng!pwd"
    )
    user = await service.register(payload)

    assert user.username == "alice"
    assert user.email == "alice@example.com"
    # Password should be hashed (bcrypt hashes start with $2)
    assert user.hashed_password.startswith("$2")


@pytest.mark.anyio
async def test_register_duplicate_username(db_session):
    service = AuthService(db_session)
    payload = UserCreate(
        username="bob", email="bob1@example.com", password="Str0ng!pwd"
    )
    await service.register(payload)

    dup_payload = UserCreate(
        username="bob", email="bob2@example.com", password="Str0ng!pwd"
    )
    with pytest.raises(DuplicateError):
        await service.register(dup_payload)


@pytest.mark.anyio
async def test_register_weak_password(db_session):
    service = AuthService(db_session)
    with pytest.raises(ValueError):
        weak = UserCreate(
            username="charlie", email="charlie@example.com", password="weakpass"
        )
        # Object creation itself raises due to schema validator
        await service.register(weak)
