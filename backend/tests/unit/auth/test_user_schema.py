import pytest
from pydantic import ValidationError
from datetime import datetime
import uuid

from app.schemas.user import UserCreate, UserRead, UserInDB


def test_user_create_valid():
    user = UserCreate(username="alice", email="alice@example.com", password="Abcd1234!")
    assert user.username == "alice"


def test_user_create_invalid_password():
    with pytest.raises(ValidationError):
        UserCreate(username="bob", email="bob@example.com", password="weak")


def test_user_read_roundtrip():
    now = datetime.utcnow()
    read = UserRead(
        id=uuid.uuid4(),
        username="carol",
        email="carol@example.com",
        created_at=now,
        updated_at=now,
    )
    serialized = read.model_dump()
    assert serialized["username"] == "carol"


def test_user_in_db_includes_hash():
    now = datetime.utcnow()
    user_in_db = UserInDB(
        id=uuid.uuid4(),
        username="dave",
        email="dave@example.com",
        created_at=now,
        updated_at=now,
        hashed_password="hash",
    )
    assert user_in_db.hashed_password == "hash" 