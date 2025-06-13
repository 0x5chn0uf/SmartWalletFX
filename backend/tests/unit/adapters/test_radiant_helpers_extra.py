from unittest.mock import MagicMock, patch

from app.adapters.protocols.radiant import RadiantContractAdapter


@patch("app.adapters.protocols.radiant.Web3")
def test_get_user_summary(mock_web3, tmp_path, monkeypatch):
    abi_path = tmp_path / "UIDataProvider.json"
    abi_path.write_text("[]")
    monkeypatch.setattr("app.core.config.settings.ARBITRUM_RPC_URL", "http://x")

    mock_contract = MagicMock()
    mock_contract.functions.getUserReservesData().call.return_value = ([], 123)
    mock_web3.return_value.eth.contract.return_value = mock_contract
    mock_web3.return_value.to_checksum_address.side_effect = lambda x: x

    with patch("app.adapters.protocols.radiant.ABI_PATH", str(abi_path)):
        adapter = RadiantContractAdapter()
        summary = adapter.get_user_summary("0xabc")
        assert summary["health_factor"] == 123 