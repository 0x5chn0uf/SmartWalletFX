import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.domain.schemas.user import UserCreate, UserInDB, UserRead


@pytest.mark.unit
def test_user_create_valid():
    username = f"alice-{uuid.uuid4().hex[:8]}"
    user = UserCreate(
        username=username,
        email=f"alice-{uuid.uuid4().hex[:8]}@example.com",
        password="Abcd1234!",
    )
    assert user.username == username


@pytest.mark.unit
def test_user_create_invalid_password():
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username=f"bob-{uuid.uuid4().hex[:8]}",
            email=f"bob-{uuid.uuid4().hex[:8]}@example.com",
            password="weak",
        )
    # Check that the error message mentions password strength
    assert "strength requirements" in str(exc_info.value)


@pytest.mark.unit
def test_user_read_roundtrip():
    now = datetime.utcnow()
    username = f"carol-{uuid.uuid4().hex[:8]}"
    read = UserRead(
        id=uuid.uuid4(),
        username=username,
        email=f"carol-{uuid.uuid4().hex[:8]}@example.com",
        created_at=now,
        updated_at=now,
        email_verified=False,
    )
    serialized = read.model_dump()
    assert serialized["username"] == username


@pytest.mark.unit
def test_user_in_db_includes_hash():
    now = datetime.utcnow()
    user_in_db = UserInDB(
        id=uuid.uuid4(),
        username=f"dave-{uuid.uuid4().hex[:8]}",
        email=f"dave-{uuid.uuid4().hex[:8]}@example.com",
        created_at=now,
        updated_at=now,
        email_verified=True,
        hashed_password="hash",
    )
    assert user_in_db.hashed_password == "hash"
