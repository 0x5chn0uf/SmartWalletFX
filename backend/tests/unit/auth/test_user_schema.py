import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserInDB, UserRead


def test_user_create_valid():
    username = f"alice-{uuid.uuid4().hex[:8]}"
    user = UserCreate(
        username=username,
        email=f"alice-{uuid.uuid4().hex[:8]}@example.com",
        password="Abcd1234!",
    )
    assert user.username == username


def test_user_create_invalid_password():
    with pytest.raises(ValidationError):
        UserCreate(
            username=f"bob-{uuid.uuid4().hex[:8]}",
            email=f"bob-{uuid.uuid4().hex[:8]}@example.com",
            password="weak",
        )


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
