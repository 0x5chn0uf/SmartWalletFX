import time
import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_wallet_crud_authenticated(authenticated_client):
    """Authenticated user can create, list, and delete their wallet."""

    # First, check what wallets already exist
    resp = await authenticated_client.get("/wallets")
    assert resp.status_code == 200
    existing_addresses = [w["address"] for w in resp.json()]

    assert len(existing_addresses) == 0

    # Generate a truly unique address using timestamp
    timestamp = int(time.time() * 1000)  # milliseconds
    unique_hex = f"{timestamp:016x}"  # 16 hex chars
    wallet_address = "0x" + unique_hex + "d" * 24  # pad to 40 chars

    wallet_payload = {
        "address": wallet_address,
        "name": "My Wallet",
    }

    # Create
    resp = await authenticated_client.post("/wallets", json=wallet_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["address"] == wallet_payload["address"]
    assert data["name"] == wallet_payload["name"]
    assert data["user_id"] is not None

    # List should contain the wallet
    resp = await authenticated_client.get("/wallets")
    assert resp.status_code == 200
    wallets = resp.json()
    assert len(wallets) == 1
    assert wallets[0]["address"] == wallet_payload["address"]

    # Delete
    resp = await authenticated_client.delete(f"/wallets/{wallet_address}")
    assert resp.status_code == 204

    # List should be empty
    resp = await authenticated_client.get("/wallets")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_wallet_crud_flow(authenticated_client):
    """Create -> list -> delete wallet flow works via API."""

    # Generate unique address using proper hex
    unique_hex = uuid.uuid4().hex + uuid.uuid4().hex
    unique_address = "0x" + unique_hex[:40]  # Take first 40 hex chars

    payload = {"address": unique_address, "name": "Test Wallet"}

    # Create
    create_resp = await authenticated_client.post("/wallets", json=payload)
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["address"].lower() == unique_address.lower()
    wallet_id = data["id"]

    # List should contain the wallet
    list_resp = await authenticated_client.get("/wallets")
    assert list_resp.status_code == 200
    wallets = list_resp.json()
    assert any(w["id"] == wallet_id for w in wallets)

    # Delete wallet
    del_resp = await authenticated_client.delete(f"/wallets/{unique_address}")
    assert del_resp.status_code == 204

    # List should now be empty
    list_resp2 = await authenticated_client.get("/wallets")
    assert list_resp2.status_code == 200
    assert list_resp2.json() == []


@pytest.mark.asyncio
async def test_wallet_duplicate_rejected(authenticated_client):
    """Creating the same wallet twice should yield 400."""

    # Generate unique address using proper hex
    unique_hex = uuid.uuid4().hex + uuid.uuid4().hex
    unique_address = "0x" + unique_hex[:40]  # Take first 40 hex chars

    payload = {"address": unique_address, "name": "Duplicate"}

    assert (
        await authenticated_client.post("/wallets", json=payload)
    ).status_code == 201
    dup = await authenticated_client.post("/wallets", json=payload)
    assert dup.status_code == 400
    assert "already exists" in dup.json()["detail"]


@pytest.mark.asyncio
async def test_wallet_invalid_address_format(authenticated_client):
    """API returns 422 for improperly formatted wallet address."""

    bad = await authenticated_client.post(
        "/wallets", json={"address": "not-an-address"}
    )
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_create_wallet_authenticated(authenticated_client: AsyncClient):
    wallet_data = {
        "address": "0x1234567890123456789012345678901234567890",
        "name": "Integration Wallet",
    }
    resp = await authenticated_client.post("/wallets", json=wallet_data)
    assert resp.status_code == 201
    json = resp.json()
    assert json["address"] == wallet_data["address"]
