import uuid

import pytest

from app.schemas.user import UserCreate
from app.services.auth_service import AuthService, DuplicateError


@pytest.mark.anyio
async def test_register_success(db_session):
    service = AuthService(db_session)
    username = f"alice-{uuid.uuid4().hex[:8]}"
    email = f"alice-{uuid.uuid4().hex[:8]}@example.com"
    payload = UserCreate(username=username, email=email, password="Str0ng!pwd")
    user = await service.register(payload)

    assert user.username == username
    assert user.email == email
    # Password should be hashed (bcrypt hashes start with $2)
    assert user.hashed_password.startswith("$2")


@pytest.mark.anyio
async def test_register_duplicate_username(db_session):
    service = AuthService(db_session)
    username = f"bob-{uuid.uuid4().hex[:8]}"
    email1 = f"bob1-{uuid.uuid4().hex[:8]}@example.com"
    email2 = f"bob2-{uuid.uuid4().hex[:8]}@example.com"
    payload = UserCreate(username=username, email=email1, password="Str0ng!pwd")
    await service.register(payload)

    dup_payload = UserCreate(username=username, email=email2, password="Str0ng!pwd")
    with pytest.raises(DuplicateError):
        await service.register(dup_payload)


@pytest.mark.anyio
async def test_register_weak_password(db_session):
    service = AuthService(db_session)
    with pytest.raises(ValueError):
        weak = UserCreate(
            username=f"charlie-{uuid.uuid4().hex[:8]}",
            email=f"charlie-{uuid.uuid4().hex[:8]}@example.com",
            password="weakpass",
        )
        # Object creation itself raises due to schema validator
        await service.register(weak)
