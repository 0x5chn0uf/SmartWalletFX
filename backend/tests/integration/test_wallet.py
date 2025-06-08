import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_create_wallet(client):
    addr = "0x9999999999999999999999999999999999999999"
    resp = client.post(
        "/wallets", json={"address": addr, "name": "Integration"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["address"] == addr
    assert data["name"] == "Integration"


def test_create_wallet_invalid_address(client):
    response = client.post("/wallets", json={"address": "invalid_address"})
    assert response.status_code == 422


def test_list_wallets(client):
    addr = "0x9999999999999999999999999999999999999999"
    resp = client.get("/wallets")
    assert resp.status_code == 200
    wallets = resp.json()
    assert any(w["address"] == addr for w in wallets)


def test_duplicate_wallet(client):
    addr = "0x9999999999999999999999999999999999999999"
    resp = client.post("/wallets", json={"address": addr})
    assert resp.status_code == 400


def test_delete_wallet(client):
    addr = "0x9999999999999999999999999999999999999999"
    resp = client.delete(f"/wallets/{addr}")
    assert resp.status_code == 204
    # Vérifie qu'il n'existe plus
    response = client.delete(
        "/wallets/0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    )
    assert response.status_code == 404


def test_delete_nonexistent_wallet(client):
    addr = "0x9999999999999999999999999999999999999999"
    resp = client.delete(f"/wallets/{addr}")
    assert resp.status_code == 404
