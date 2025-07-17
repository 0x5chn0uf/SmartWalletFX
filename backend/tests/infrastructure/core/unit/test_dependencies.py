import uuid
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.api.dependencies import auth_deps


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
async def test_get_current_user_success():
    """A valid token payload on request state returns the user instance."""
    user_id = uuid.uuid4()
    user = DummyUser(id=user_id)
    session = DummySession(user)

    payload = {"sub": str(user_id), "roles": ["user"], "attributes": {}}
    request = Mock(state=Mock(token_payload=payload))

    result = await auth_deps.get_current_user(request=request, db=session)

    assert result is user
    assert hasattr(result, "_current_roles")
    assert result._current_roles == ["user"]
    assert hasattr(result, "_current_attributes")
    assert result._current_attributes == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "state_payload, session_user, expected_detail",
    [
        (None, None, "Not authenticated"),
        ({}, None, "Invalid subject in token"),
        ({"sub": "abc"}, None, "Invalid subject in token"),
        ({"sub": str(uuid.uuid4())}, None, "User not found"),
    ],
)
async def test_get_current_user_error_paths(
    state_payload, session_user, expected_detail
):
    """Verify each error branch raises HTTPException with the correct detail message."""
    request = Mock(state=Mock(token_payload=state_payload))
    session = DummySession(user=session_user)

    with pytest.raises(HTTPException) as exc:
        await auth_deps.get_current_user(request=request, db=session)

    assert exc.value.status_code == 401
    assert expected_detail in exc.value.detail
