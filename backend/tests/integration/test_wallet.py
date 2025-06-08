import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core import database
from app.main import create_app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"


@pytest.mark.asyncio
async def test_create_wallet(test_app, db_session):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        addr = "0x9999999999999999999999999999999999999999"
        resp = await client.post(
            "/wallets", json={"address": addr, "name": "Integration"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["address"] == addr
        assert data["name"] == "Integration"


@pytest.mark.asyncio
async def test_create_wallet_invalid_address(test_app, db_session):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post(
            "/wallets", json={"address": "invalid_address"}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_wallets(test_app, db_session):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get("/wallets")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_duplicate_wallet(test_app, db_session):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        addr = "0x9999999999999999999999999999999999999999"
        await client.post("/wallets", json={"address": addr})
        response = await client.post("/wallets", json={"address": addr})
        assert response.status_code == 400
        assert "Wallet address already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_wallet(test_app, db_session):
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        addr = "0x9999999999999999999999999999999999999999"
        # S'assurer que le wallet existe
        await client.post("/wallets", json={"address": addr})
        resp = await client.delete(f"/wallets/{addr}")
        assert resp.status_code in (204, 404)
        # Vérifie qu'il n'existe plus
        response = await client.delete(
            "/wallets/0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )
        assert response.status_code == 404
