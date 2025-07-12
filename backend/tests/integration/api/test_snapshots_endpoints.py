import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.user import User
from app.models.wallet import Wallet
from app.repositories.wallet_repository import WalletRepository

client = TestClient(app)


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_returns_200(
    db_session, authenticated_client: AsyncClient, test_user
):
    """
    Given an authenticated user and a wallet they own,
    When they request portfolio snapshots for that wallet,
    Then the response should be successful (200 OK).
    """
    # The `authenticated_client` is logged in as the `test_user`
    # so we can use that user's ID to create the wallet.
    wallet = await WalletRepository(db_session).create(
        user_id=test_user.id,
        address=f"0x{uuid.uuid4().hex[:40]}",
        name="Test Wallet",
    )
    response = await authenticated_client.get(
        f"/wallets/{wallet.address}/portfolio/snapshots"
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_portfolio_snapshots_for_nonexistent_wallet_returns_404(
    authenticated_client: AsyncClient,
):
    non_existent_address = "0xnotarealaddress"
    response = await authenticated_client.get(
        f"/wallets/{non_existent_address}/portfolio/snapshots"
    )
    assert response.status_code == 404
