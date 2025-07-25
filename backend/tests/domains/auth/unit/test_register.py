import uuid

import pytest

from app.domain.schemas.user import UserCreate
from app.usecase.auth_usecase import DuplicateError


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_success(auth_usecase, mock_user_repo):
    """Test successful user registration with new DI pattern."""
    # Enable side effects for registration tests
    mock_user_repo.get_by_username.side_effect = mock_user_repo._username_side_effect
    mock_user_repo.get_by_email.side_effect = mock_user_repo._email_side_effect
    # Clear return_value to ensure side effect is used
    mock_user_repo.save.return_value = None

    username = f"alice-{uuid.uuid4().hex[:8]}"
    email = f"alice-{uuid.uuid4().hex[:8]}@example.com"
    payload = UserCreate(username=username, email=email, password="Str0ng!pwd")
    user = await auth_usecase.register(payload)

    assert user.username == username
    assert user.email == email
    # Password should be hashed (bcrypt hashes start with $2)
    assert user.hashed_password.startswith("$2")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_duplicate_username(auth_usecase, mock_user_repo):
    """Test that registering with duplicate username raises DuplicateError."""
    # Enable side effects for registration tests
    mock_user_repo.get_by_username.side_effect = mock_user_repo._username_side_effect
    mock_user_repo.get_by_email.side_effect = mock_user_repo._email_side_effect
    # Clear return_value to ensure side effect is used
    mock_user_repo.save.return_value = None

    username = f"bob-{uuid.uuid4().hex[:8]}"
    email1 = f"bob1-{uuid.uuid4().hex[:8]}@example.com"
    email2 = f"bob2-{uuid.uuid4().hex[:8]}@example.com"
    payload = UserCreate(username=username, email=email1, password="Str0ng!pwd")
    await auth_usecase.register(payload)

    dup_payload = UserCreate(username=username, email=email2, password="Str0ng!pwd")
    with pytest.raises(DuplicateError):
        await auth_usecase.register(dup_payload)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_weak_password(auth_usecase):
    """Test that registering with weak password raises ValidationError."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        weak = UserCreate(
            username=f"charlie-{uuid.uuid4().hex[:8]}",
            email=f"charlie-{uuid.uuid4().hex[:8]}@example.com",
            password="weakpass",
        )
        # Object creation itself raises due to schema validator
        await auth_usecase.register(weak)
