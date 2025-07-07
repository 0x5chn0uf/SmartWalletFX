import uuid

import pytest
from jose.exceptions import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import auth_deps
from app.models.user import User
from app.utils.jwt import JWTUtils


class DummySession(AsyncSession):
    """Lightweight stub of AsyncSession get method only."""

    def __init__(self, user: User | None):
        self._user = user

    async def get(self, entity, ident):  # type: ignore[override]
        return self._user


@pytest.mark.asyncio
async def test_get_current_user_success(monkeypatch):
    user = User(
        id=uuid.uuid4(),
        username=f"alice-{uuid.uuid4().hex[:8]}",
        email=f"a-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="x",
    )

    def _dummy_decode(token: str):  # noqa: D401
        return {"sub": str(uuid.uuid4()), "roles": ["user"]}

    monkeypatch.setattr(JWTUtils, "decode_token", staticmethod(_dummy_decode))
    dummy_db = DummySession(user)

    result = await auth_deps.get_current_user(token="dummy", db=dummy_db)  # type: ignore[arg-type]
    assert result is user


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(monkeypatch):
    def _raise(_token: str):  # noqa: D401
        raise JWTError("invalid")

    monkeypatch.setattr(JWTUtils, "decode_token", staticmethod(_raise))
    dummy_db = DummySession(None)

    with pytest.raises(Exception):
        await auth_deps.get_current_user(token="bad", db=dummy_db)  # type: ignore[arg-type]
