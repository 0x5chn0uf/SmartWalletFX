import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.api.dependencies import get_user_from_request


class DummyUser:
    def __init__(self, id):
        self.id = id


class DummySession:  # noqa: D101 – async session stub
    def __init__(self, user: DummyUser | None):
        self._user = user

    async def get(self, model, pk):  # noqa: D401 – mimic SQLAlchemy AsyncSession.get
        if self._user and self._user.id == pk:
            return self._user
        return None


@pytest.mark.asyncio
async def test_get_user_from_request_success():
    """A valid user_id and token payload on request state returns the user instance."""
    user_id = uuid.uuid4()
    user = DummyUser(id=user_id)
    session = DummySession(user)

    payload = {"sub": str(user_id), "roles": ["user"], "attributes": {}}
    request = Mock(state=Mock(user_id=user_id, token_payload=payload))

    # Mock the DIContainer and database service
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__.return_value = session

    mock_database = Mock()
    mock_database.get_session.return_value = mock_session_context

    mock_di_container = Mock()
    mock_di_container.get_core.return_value = mock_database

    with patch("app.di.DIContainer", return_value=mock_di_container):
        result = await get_user_from_request(request=request)

        assert result is user
        assert hasattr(result, "_current_roles")
        assert result._current_roles == ["user"]
        assert hasattr(result, "_current_attributes")
        assert result._current_attributes == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, token_payload, session_user, expected_detail",
    [
        (None, {"sub": "test", "roles": []}, None, "Not authenticated"),
        (uuid.uuid4(), None, None, "Not authenticated"),
        (uuid.uuid4(), {"sub": "test", "roles": []}, None, "User not found"),
    ],
)
async def test_get_user_from_request_error_paths(
    user_id, token_payload, session_user, expected_detail
):
    """Verify each error branch raises HTTPException with the correct detail message."""
    request = Mock(state=Mock(user_id=user_id, token_payload=token_payload))
    session = DummySession(user=session_user)

    # Mock the DIContainer and database service
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__.return_value = session

    mock_database = Mock()
    mock_database.get_session.return_value = mock_session_context

    mock_di_container = Mock()
    mock_di_container.get_core.return_value = mock_database

    with patch("app.di.DIContainer", return_value=mock_di_container):
        with pytest.raises(HTTPException) as exc:
            await get_user_from_request(request=request)

        assert exc.value.status_code == 401
        assert expected_detail in exc.value.detail
