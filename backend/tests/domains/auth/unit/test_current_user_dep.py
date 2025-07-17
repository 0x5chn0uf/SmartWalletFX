import uuid
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import auth_deps
from app.models.user import User


class DummySession(AsyncSession):
    """Lightweight stub of AsyncSession get method only."""

    def __init__(self, user: User | None):
        self._user = user

    async def get(self, entity, ident):  # type: ignore[override]
        if self._user and self._user.id == ident:
            return self._user
        return None


@pytest.mark.asyncio
async def test_get_current_user_success():
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        username=f"alice-{uuid.uuid4().hex[:8]}",
        email=f"a-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="x",
    )

    payload = {"sub": str(user_id), "roles": ["user"], "attributes": {}}
    request = Mock(state=Mock(token_payload=payload))
    dummy_db = DummySession(user)

    result = await auth_deps.get_current_user(request=request, db=dummy_db)
    assert result is user


@pytest.mark.asyncio
async def test_get_current_user_no_payload():
    request = Mock(state=Mock(token_payload=None))
    dummy_db = DummySession(None)

    with pytest.raises(HTTPException) as exc:
        await auth_deps.get_current_user(request=request, db=dummy_db)

    assert exc.value.status_code == 401
    assert "Not authenticated" in exc.value.detail
