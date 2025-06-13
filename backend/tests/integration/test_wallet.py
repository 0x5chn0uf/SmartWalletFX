import httpx
import pytest
from httpx import AsyncClient

# Use a consistent, unique address for this test file to avoid conflicts
ADDRESS = "0x1234567890123456789012345678901234567890"


@pytest.mark.asyncio
async def test_wallet_full_crud_lifecycle(test_app, db_session):
    """
    Tests the complete lifecycle of a wallet:
    1. Initial list is empty.
    2. Create a wallet.
    3. List contains the new wallet.
    4. Try to create a duplicate (should fail).
    5. Delete the wallet.
    6. List is empty again.
    7. Try to delete a non-existent wallet (should fail).
    """
    transport = httpx.ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        # 1. Initial list should be empty (due to clean_db fixture)
        initial_list_resp = await client.get("/wallets")
        assert initial_list_resp.status_code == 200
        assert initial_list_resp.json() == []

        # 2. Create a new wallet
        create_payload = {
            "address": ADDRESS,
            "name": "Integration Test Wallet",
        }
        create_resp = await client.post("/wallets", json=create_payload)
        assert create_resp.status_code == 201
        created_data = create_resp.json()
        assert created_data["address"] == ADDRESS
        assert created_data["name"] == "Integration Test Wallet"

        # 3. List should now contain the new wallet
        list_resp = await client.get("/wallets")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert len(list_data) == 1
        assert list_data[0]["address"] == ADDRESS

        # 4. Attempt to create a duplicate wallet
        duplicate_resp = await client.post("/wallets", json=create_payload)
        assert duplicate_resp.status_code == 400
        assert "already exists" in duplicate_resp.json()["detail"]

        # 5. Delete the created wallet
        delete_resp = await client.delete(f"/wallets/{ADDRESS}")
        assert delete_resp.status_code == 204

        # 6. List should be empty again
        final_list_resp = await client.get("/wallets")
        assert final_list_resp.status_code == 200
        assert final_list_resp.json() == []

        # 7. Attempt to delete a wallet that does not exist
        non_existent_delete_resp = await client.delete(f"/wallets/{ADDRESS}")
        assert non_existent_delete_resp.status_code == 404
        assert "not found" in non_existent_delete_resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_wallet_with_invalid_address_format(test_app, db_session):
    """
    Ensure the API returns a 422 Unprocessable Entity error for an
    improperly formatted wallet address.
    """
    transport = httpx.ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/wallets", json={"address": "this-is-not-a-valid-address"}
        )
        assert response.status_code == 422
