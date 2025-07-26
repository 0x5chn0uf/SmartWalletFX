import uuid

import pytest
from fastapi import FastAPI, status
from starlette.testclient import TestClient

from app.api.endpoints.users import Users
from app.domain.schemas.user import UserRead


class _FakeRepo:
    def __init__(self, user=None):
        self._user = user

    async def get_by_id(self, uid):
        return self._user


class _FakeUsecase:
    async def get_profile(self, user_id: str):  # noqa: D401 – fake
        return UserRead(id=uuid.uuid4(), username="alice", email="a@example.com")


def _app(user=None):
    repo = _FakeRepo(user)
    Users(repo, _FakeUsecase(), None)
    app = FastAPI()
    app.include_router(Users.ep)

    @app.middleware("http")
    async def _inject_user(request, call_next):
        uid = user.id if user else uuid.uuid4()
        request.state.user_id = uid
        request.state.token_payload = {"sub": str(uid)}
        return await call_next(request)

    return app


@pytest.mark.asyncio
async def test_read_current_user_success():
    from datetime import datetime

    fake_user = UserRead(
        id=uuid.uuid4(),
        username="alice",
        email="a@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        email_verified=True,
    )
    client = TestClient(_app(user=fake_user))
    resp = client.get("/users/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


@pytest.mark.asyncio
async def test_read_current_user_not_found():
    client = TestClient(_app(user=None))
    resp = client.get("/users/me")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
