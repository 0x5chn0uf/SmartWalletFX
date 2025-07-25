import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_user_from_request
from app.models.user import User


class DummySession(AsyncSession):
    """Lightweight stub of AsyncSession get method only."""

    def __init__(self, user: User | None):
        self._user = user

    async def get(self, entity, ident):  # type: ignore[override]
        if self._user and self._user.id == ident:
            return self._user
        return None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_from_request_success():
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        username=f"alice-{uuid.uuid4().hex[:8]}",
        email=f"a-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="x",
    )

    payload = {"sub": str(user_id), "roles": ["user"], "attributes": {}}
    request = Mock(state=Mock(user_id=user_id, token_payload=payload))
    dummy_db = DummySession(user)

    # Mock the DIContainer and database service
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__.return_value = dummy_db

    mock_database = Mock()
    mock_database.get_session.return_value = mock_session_context

    mock_di_container = Mock()
    mock_di_container.get_core.return_value = mock_database

    with patch("app.main.di_container", mock_di_container):
        result = await get_user_from_request(request=request)
        assert result is user
        assert result._current_roles == ["user"]
        assert result._current_attributes == {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_from_request_no_user_id():
    request = Mock(state=Mock(user_id=None, token_payload={"sub": "test", "roles": []}))

    with pytest.raises(HTTPException) as exc:
        await get_user_from_request(request=request)

    assert exc.value.status_code == 401
    assert "Not authenticated" in exc.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_from_request_no_payload():
    user_id = uuid.uuid4()
    request = Mock(state=Mock(user_id=user_id, token_payload=None))

    with pytest.raises(HTTPException) as exc:
        await get_user_from_request(request=request)

    assert exc.value.status_code == 401
    assert "Not authenticated" in exc.value.detail
