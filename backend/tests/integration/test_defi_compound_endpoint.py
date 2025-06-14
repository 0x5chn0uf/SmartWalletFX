import pytest
import httpx
from unittest.mock import MagicMock, ANY, AsyncMock, patch
from web3 import Web3
from app.main import app
from httpx import AsyncClient
from datetime import datetime
from app.schemas.defi import DeFiAccountSnapshot

TEST_ADDRESS = "0x1111111111111111111111111111111111111111"

@pytest.fixture
def mock_w3_compound():
    w3 = MagicMock()
    w3.eth = MagicMock()

    mock_comptroller_contract = MagicMock()
    mock_comptroller_contract.functions.getAssetsIn(ANY).call.return_value = ["0xc00e94Cb662C3520282E6f5717214004A7f26888"]
    
    mock_ctoken_contract = MagicMock()
    mock_ctoken_contract.functions.underlying().call.return_value = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    mock_ctoken_contract.functions.balanceOf(ANY).call.return_value = 100 * 10**8
    mock_ctoken_contract.functions.borrowBalanceCurrent(ANY).call.return_value = 50 * 10**18
    mock_ctoken_contract.functions.exchangeRateCurrent().call.return_value = 20000000000000000

    def contract_side_effect(address, abi):
        if address == "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b":
            return mock_comptroller_contract
        else:
            return mock_ctoken_contract

    w3.eth.contract.side_effect = contract_side_effect
    return w3, mock_comptroller_contract

@pytest.mark.asyncio
@patch("app.usecase.defi_compound_usecase.CompoundUsecase.get_user_snapshot")
async def test_get_compound_user_data_success(mock_get_snapshot, test_app):
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
        response = await ac.get("/defi/compound/0x123")
    assert response.status_code == 200
    mock_get_snapshot.assert_called_once_with("0x123")
    data = response.json()
    assert data["user_address"] == "0x123"

@pytest.mark.asyncio
@patch("app.usecase.defi_compound_usecase.CompoundUsecase.get_user_snapshot")
async def test_get_compound_user_data_not_found(mock_get_snapshot, test_app):
    mock_get_snapshot.return_value = None
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.get("/defi/compound/0x456")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "User data not found on Compound.",
    }
    mock_get_snapshot.assert_called_once_with("0x456") 