from unittest.mock import MagicMock, patch

import pytest

from app.adapters.radiant_contract_adapter import (
    RadiantAdapterError,
    RadiantContractAdapter,
)


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.settings.ARBITRUM_RPC_URL", "http://mock-rpc"
    )


@pytest.mark.asyncio
@patch("app.adapters.radiant_contract_adapter.Web3")
async def test_init_missing_rpc_url(mock_web3, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ARBITRUM_RPC_URL", None)
    with pytest.raises(RadiantAdapterError):
        RadiantContractAdapter()


@pytest.mark.asyncio
@patch("app.adapters.radiant_contract_adapter.Web3")
async def test_get_user_data_success(mock_web3, mock_settings, tmp_path):
    # Patch ABI loading
    abi_path = tmp_path / "UIDataProvider.json"
    abi_path.write_text("[]")
    with patch(
        "app.adapters.radiant_contract_adapter.ABI_PATH", str(abi_path)
    ):
        # Mock contract call
        mock_contract = MagicMock()
        mock_contract.functions.getUserReservesData().call.return_value = (
            [
                ("0xToken", 1000, True, 0, 0, 0),
            ],
            2.5,
        )
        mock_web3.return_value.eth.contract.return_value = mock_contract
        adapter = RadiantContractAdapter(rpc_url="http://mock-rpc")
        with patch.object(
            adapter, "get_token_metadata", return_value=("MOCK", 18)
        ):
            result = adapter.get_user_data("0xUser")
            assert result["reserves"][0]["token_address"] == "0xToken"
            assert result["reserves"][0]["symbol"] == "MOCK"
            assert result["reserves"][0]["supplied"] == 1000
            assert result["health_factor"] == 2.5


@pytest.mark.asyncio
@patch("app.adapters.radiant_contract_adapter.Web3")
async def test_get_token_metadata_success(mock_web3, mock_settings):
    mock_token = MagicMock()
    mock_token.functions.symbol().call.return_value = "MOCK"
    mock_token.functions.decimals().call.return_value = 8
    mock_web3.return_value.eth.contract.return_value = mock_token
    adapter = RadiantContractAdapter(rpc_url="http://mock-rpc")
    symbol, decimals = adapter.get_token_metadata("0xToken")
    assert symbol == "MOCK"
    assert decimals == 8


@pytest.mark.asyncio
@patch("app.adapters.radiant_contract_adapter.Web3")
async def test_to_usd(mock_web3, mock_settings):
    adapter = RadiantContractAdapter(rpc_url="http://mock-rpc")
    assert adapter.to_usd(12345, "MOCK") == 12345.0
