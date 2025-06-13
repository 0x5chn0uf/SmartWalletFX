import httpx
import pytest

ADDRESS = "0x1111111111111111111111111111111111111111"


@pytest.mark.asyncio
async def test_wallet_crud_flow(test_app):
    """Create -> list -> delete wallet flow works via API."""
    payload = {"address": ADDRESS, "name": "Test Wallet"}

    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=True)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        # Create
        create_resp = await ac.post("/wallets", json=payload)
        assert create_resp.status_code == 201
        data = create_resp.json()
        assert data["address"].lower() == ADDRESS.lower()
        wallet_id = data["id"]

        # List should contain the wallet
        list_resp = await ac.get("/wallets")
        assert list_resp.status_code == 200
        wallets = list_resp.json()
        assert any(w["id"] == wallet_id for w in wallets)

        # Delete wallet
        del_resp = await ac.delete(f"/wallets/{ADDRESS}")
        assert del_resp.status_code == 204

        # List should now be empty
        list_resp2 = await ac.get("/wallets")
        assert list_resp2.status_code == 200
        assert list_resp2.json() == []
