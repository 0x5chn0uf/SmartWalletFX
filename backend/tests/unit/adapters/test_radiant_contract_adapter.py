from unittest.mock import MagicMock, patch

import pytest

from app.adapters.radiant_contract_adapter import (
    RadiantAdapterError,
    RadiantContractAdapter,
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


@pytest.fixture()
def adapter(monkeypatch, tmp_path):
    """Return a RadiantContractAdapter instance with on-chain calls mocked."""
    monkeypatch.setattr(
        "app.core.config.settings.ARBITRUM_RPC_URL", "http://mock-rpc"
    )
    abi_path = tmp_path / "UIDataProvider.json"
    abi_path.write_text("[]")

    with patch(
        "app.adapters.radiant_contract_adapter.ABI_PATH", str(abi_path)
    ), patch("app.adapters.radiant_contract_adapter.Web3") as mock_web3:
        mock_contract = MagicMock()
        mock_contract.functions.getReservesData().call.return_value = (
            [("0xToken",)],
        )
        mock_contract.functions.getUserReservesData().call.return_value = (
            [],
            1234,
        )
        mock_web3.return_value.eth.contract.return_value = mock_contract
        mock_web3.return_value.to_checksum_address.side_effect = lambda x: x

        adapter_instance = RadiantContractAdapter(rpc_url="http://mock-rpc")
        adapter_instance.get_token_metadata = lambda _addr: ("MOCK", 18)
        return adapter_instance


@patch("app.adapters.radiant_contract_adapter.requests.get")
def test_get_token_price_cache(mock_get, adapter):
    mock_get.return_value.json.return_value = {"usd-coin": {"usd": 1.0}}
    mock_get.return_value.raise_for_status = lambda: None

    usdc_addr = "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    price_first = adapter.get_token_price(usdc_addr)
    assert price_first == 1.0

    mock_get.side_effect = RuntimeError("HTTP call should be cached")
    price_second = adapter.get_token_price(usdc_addr)
    assert price_second == 1.0


def test_reserves_health_summary(adapter):
    reserves = adapter.get_reserves_data()
    assert reserves and reserves[0]["symbol"] == "MOCK"

    health = adapter.get_health_factor("0xUser")
    assert health == 1234.0

    summary = adapter.get_user_summary("0xUser")
    assert summary["health_factor"] == 1234


@pytest.mark.asyncio
async def test_async_get_user_data_wrapper(adapter, monkeypatch):
    """Ensure the async wrapper correctly calls the sync method."""
    mock_sync_data = {"reserves": [], "health_factor": 1.0}

    def mock_get_user_data(user_address):
        return mock_sync_data

    monkeypatch.setattr(adapter, "get_user_data", mock_get_user_data)

    result = await adapter.async_get_user_data("0xTest")
    assert result == mock_sync_data


@patch("app.adapters.radiant_contract_adapter.Web3")
def test_error_handling_paths(mock_web3, monkeypatch, tmp_path):
    """Test various error conditions."""
    # Setup for other error tests
    abi_path = tmp_path / "UIDataProvider.json"
    abi_path.write_text("[]")
    monkeypatch.setattr(
        "app.core.config.settings.ARBITRUM_RPC_URL", "http://mock-rpc"
    )

    with patch(
        "app.adapters.radiant_contract_adapter.ABI_PATH", str(abi_path)
    ):
        # 2. get_user_data failure
        mock_contract_fail = MagicMock()
        mock_contract_fail.functions.getUserReservesData().call.side_effect = (
            Exception("RPC Error")
        )  # noqa: E501
        mock_web3.return_value.eth.contract.return_value = mock_contract_fail
        adapter_fail = RadiantContractAdapter()
        with pytest.raises(
            RadiantAdapterError,
            match="RadiantContractAdapter error",
        ):
            adapter_fail.get_user_data("0xUser")

        # 3. get_token_metadata failure
        mock_token_contract = MagicMock()
        mock_token_contract.functions.symbol().call.side_effect = Exception(
            "Metadata Error"
        )  # noqa: E501
        mock_web3.return_value.eth.contract.return_value = mock_token_contract
        # This should now return the default "UNKNOWN" tuple,
        # not raise an error
        symbol, decimals = adapter_fail.get_token_metadata("0xToken")
        assert symbol == "UNKNOWN"
        assert decimals == 18

        # 4. get_reserves_data failure
        mock_contract_fail.functions.getReservesData().call.side_effect = (
            Exception("Reserves Error")
        )  # noqa: E501
        with pytest.raises(
            RadiantAdapterError,
            match="get_reserves_data error",
        ):
            adapter_fail.get_reserves_data()
