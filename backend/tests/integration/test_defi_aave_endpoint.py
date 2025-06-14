import pytest
from unittest.mock import MagicMock, ANY, patch
from app.main import app
from httpx import AsyncClient
from datetime import datetime
from app.schemas.defi import DeFiAccountSnapshot

AAVE_DECIMALS = 10**18

@pytest.fixture
def mock_w3():
    w3 = MagicMock()
    w3.eth = MagicMock()
    
    # Mock chain of calls
    mock_provider_contract = MagicMock()
    mock_provider_contract.functions.getPool().call.return_value = "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"
    
    mock_lending_pool_contract = MagicMock()
    user_account_data = (2000000000000000000, 1000000000000000000, 1000000000000000000, 500000000000000000, 500000000000000000, 2000000000000000000)
    mock_lending_pool_contract.functions.getUserAccountData(ANY).call.return_value = user_account_data
    
    def contract_side_effect(address, abi):
        if address == "0xB53C1a33016B2DC2fF3653530bfF1848a515c8c5":
            return mock_provider_contract
        else:
            return mock_lending_pool_contract

    w3.eth.contract.side_effect = contract_side_effect
    return w3

@pytest.mark.asyncio
@patch("app.usecase.defi_aave_usecase.AaveUsecase.get_user_snapshot")
async def test_get_aave_user_data_success(mock_get_snapshot, test_app):
    mock_snapshot = DeFiAccountSnapshot(
        user_address="0x123",
        timestamp=int(datetime.utcnow().timestamp()),
        collaterals=[],
        borrowings=[],
        staked_positions=[],
        health_scores=[],
        total_apy=None,
    )
    mock_get_snapshot.return_value = mock_snapshot
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.get("/defi/aave/0x123")
    assert response.status_code == 200
    mock_get_snapshot.assert_called_once_with("0x123")
    data = response.json()
    assert data["user_address"] == "0x123"

@pytest.mark.asyncio
@patch("app.usecase.defi_aave_usecase.AaveUsecase.get_user_snapshot")
async def test_get_aave_user_data_not_found(mock_get_snapshot, test_app):
    mock_get_snapshot.return_value = None
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.get("/defi/aave/0x456")
    assert response.status_code == 404
    assert response.json() == {"detail": "User data not found on Aave."}
    mock_get_snapshot.assert_called_once_with("0x456")

@pytest.mark.asyncio
async def test_aave_and_compound_endpoints(mock_w3, monkeypatch):
    """Aave and Compound endpoints propagate mocked snapshots."""
    from app.schemas.defi import DeFiAccountSnapshot
    from app.api.endpoints.defi import get_aave_usecase, get_compound_usecase
    from app.usecase.defi_aave_usecase import AaveUsecase
    from app.usecase.defi_compound_usecase import CompoundUsecase

    async def _mock_snapshot(address: str):
        return DeFiAccountSnapshot(
            user_address=address,
            timestamp=123,
            collaterals=[],
            borrowings=[],
            staked_positions=[],
            health_scores=[],
            total_apy=None,
        )

    class MockAaveUsecase:
        async def get_user_snapshot(self, address: str):
            return await _mock_snapshot(address)

    class MockCompoundUsecase:
        async def get_user_snapshot(self, address: str):
            return await _mock_snapshot(address)

    app.dependency_overrides[get_aave_usecase] = MockAaveUsecase
    app.dependency_overrides[get_compound_usecase] = MockCompoundUsecase

    transport = AsyncClient(app=app, base_url="http://test")
    async with transport as client:
        aave_resp = await client.get("/defi/aave/0x123")
        compound_resp = await client.get("/defi/compound/0x123")

    assert aave_resp.status_code == 200
    assert compound_resp.status_code == 200

    del app.dependency_overrides[get_aave_usecase]
    del app.dependency_overrides[get_compound_usecase]
