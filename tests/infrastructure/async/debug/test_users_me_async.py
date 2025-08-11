import httpx
import pytest


@pytest.fixture(autouse=True)
def no_patch_httpx_async_client():
    pass


@pytest.mark.asyncio
async def test_users_me_endpoint(test_app_with_di_container, test_di_container_with_db):
    user_repo = test_di_container_with_db.get_repository("user")
    payload = {
        "username": "bob_async",
        "email": "bob_async@example.com",
        "password": "Str0ng!pwd",
    }

    transport = httpx.ASGITransport(app=test_app_with_di_container)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/auth/register", json=payload)
        assert resp.status_code == 201
        user = await user_repo.get_by_email(payload["email"])
        user.email_verified = True
        await user_repo.save(user)
        resp = await client.post(
            "/auth/token",
            data={"username": payload["username"], "password": payload["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        resp = await client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == payload["username"]
