import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.xfail(
    reason="/users/me endpoint not yet implemented (Subtask 4.10)"
)


@pytest.mark.asyncio
async def test_users_me_requires_auth(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        resp = await ac.get("/users/me")
    assert resp.status_code == 401
