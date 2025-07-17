import uuid

import pytest

from app.domain.schemas.user import UserCreate, WeakPasswordError
from app.services.auth_service import DuplicateError


@pytest.mark.asyncio
async def test_register_success(auth_service):
    """Test successful user registration with new DI pattern."""
    username = f"alice-{uuid.uuid4().hex[:8]}"
    email = f"alice-{uuid.uuid4().hex[:8]}@example.com"
    payload = UserCreate(username=username, email=email, password="Str0ng!pwd")
    user = await auth_service.register(payload)

    assert user.username == username
    assert user.email == email
    # Password should be hashed (bcrypt hashes start with $2)
    assert user.hashed_password.startswith("$2")


@pytest.mark.asyncio
async def test_register_duplicate_username(auth_service):
    """Test that registering with duplicate username raises DuplicateError."""
    username = f"bob-{uuid.uuid4().hex[:8]}"
    email1 = f"bob1-{uuid.uuid4().hex[:8]}@example.com"
    email2 = f"bob2-{uuid.uuid4().hex[:8]}@example.com"
    payload = UserCreate(username=username, email=email1, password="Str0ng!pwd")
    await auth_service.register(payload)

    dup_payload = UserCreate(username=username, email=email2, password="Str0ng!pwd")
    with pytest.raises(DuplicateError):
        await auth_service.register(dup_payload)


@pytest.mark.asyncio
async def test_register_weak_password(auth_service):
    """Test that registering with weak password raises WeakPasswordError."""
    with pytest.raises(WeakPasswordError):
        weak = UserCreate(
            username=f"charlie-{uuid.uuid4().hex[:8]}",
            email=f"charlie-{uuid.uuid4().hex[:8]}@example.com",
            password="weakpass",
        )
        # Object creation itself raises due to schema validator
        await auth_service.register(weak)
