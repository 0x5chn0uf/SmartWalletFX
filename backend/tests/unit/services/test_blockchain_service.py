"""
Unit tests for BlockchainService.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from app.schemas.defi import ProtocolName
from app.services.blockchain_service import BlockchainService


class TestBlockchainService:
    """Test cases for BlockchainService."""

    @pytest.fixture
    def blockchain_service(self):
        """Blockchain service instance."""
        return BlockchainService()

    @pytest.fixture
    def mock_web3(self):
        """Mock Web3 instance."""
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = True
        return mock_w3

    @pytest.mark.asyncio
    async def test_get_wallet_balances_success(self, mock_web3):
        """Test getting wallet balances successfully."""
        with patch("app.services.blockchain_service.Web3") as mock_web3_class, patch(
            "app.services.blockchain_service.settings"
        ) as mock_settings:
            # Configure settings
            mock_settings.WEB3_PROVIDER_URI = "http://localhost:8545"

            # Prepare mock provider returned by Web3.HTTPProvider
            mock_web3_class.HTTPProvider.return_value = mock_web3

            # Prepare w3 instance that will be returned by calling Web3(...)
            w3_instance = Mock()
            w3_instance.is_connected.return_value = True
            mock_web3_class.return_value = w3_instance

            # Patch Web3.to_checksum_address to return the same address for simplicity
            mock_web3_class.to_checksum_address.side_effect = lambda addr: addr

            # Mock contract with proper function call chains
            mock_contract = Mock()
            # balanceOf chain
            mock_balance_call = Mock()
            mock_balance_call.call.return_value = 1000000000000000000  # 1 ETH
            mock_contract.functions.balanceOf.return_value = mock_balance_call
            # decimals chain
            mock_decimals_call = Mock()
            mock_decimals_call.call.return_value = 18
            mock_contract.functions.decimals.return_value = mock_decimals_call

            # Ensure w3.eth.contract returns our mock_contract
            w3_instance.eth.contract.return_value = mock_contract

            # Instantiate service AFTER all mocks are configured
            blockchain_service = BlockchainService()

            # Execute
            balances = await blockchain_service.get_wallet_balances(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"],
            )

            # Assertions
            assert "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" in balances
            token_data = balances["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"]
            assert token_data["balance_wei"] == 1000000000000000000
            assert token_data["decimals"] == 18

    @pytest.mark.asyncio
    async def test_get_wallet_balances_no_web3(self, blockchain_service):
        """Test getting wallet balances when Web3 is not available."""
        blockchain_service.w3 = None

        balances = await blockchain_service.get_wallet_balances(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert balances == {}

    @pytest.mark.asyncio
    async def test_get_wallet_balances_contract_error(
        self, blockchain_service, mock_web3
    ):
        """Test getting wallet balances with contract error."""
        with patch("app.services.blockchain_service.Web3") as mock_web3_class:
            mock_web3_class.HTTPProvider.return_value = mock_web3
            mock_web3_class.to_checksum_address.return_value = (
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            # Mock contract that raises error
            mock_contract = Mock()
            mock_contract.functions.balanceOf.return_value.call.side_effect = Exception(
                "Contract error"
            )

            mock_web3.eth.contract.return_value = mock_contract

            balances = await blockchain_service.get_wallet_balances(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"],
            )

            assert balances == {}

    @pytest.mark.asyncio
    async def test_get_token_price_coingecko_success(self):
        """Test getting token price from CoinGecko successfully."""
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value.status = 200
        mock_response.__aenter__.return_value.json = AsyncMock(
            return_value={"0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {"usd": 3000.0}}
        )

        async def _fake_session(*args, **kwargs):
            return mock_response

        with patch("aiohttp.ClientSession", _fake_session):
            service = BlockchainService()
            # Ensure Chainlink path returns None to use CoinGecko
            with patch.object(service, "_get_price_from_chainlink", return_value=None):
                price = await service.get_token_price(
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
                )

                assert price == 3000.0

    @pytest.mark.asyncio
    async def test_get_token_price_chainlink_success(
        self, blockchain_service, mock_web3
    ):
        """Test getting token price from Chainlink successfully."""
        # Mock Web3 setup
        with patch("app.services.blockchain_service.Web3") as mock_web3_class:
            mock_web3_class.HTTPProvider.return_value = mock_web3
            mock_web3_class.to_checksum_address.return_value = (
                "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
            )

            # Prepare Web3 instance and contract chain mocks
            web3_instance = Mock()
            web3_instance.is_connected.return_value = True

            # Mock Chainlink contract and latestRoundData call chain
            mock_contract = Mock()
            mock_latest = Mock()
            mock_latest.call.return_value = [
                1,
                300000000000,  # 3000 USD (8 decimals)
                1234567890,
                1234567890,
                1,
            ]
            mock_contract.functions.latestRoundData.return_value = mock_latest

            web3_instance.eth.contract.return_value = mock_contract

            # Configure the patched Web3 class to return our prepared instance
            mock_web3_class.return_value = web3_instance

            # Instantiate service AFTER patching Web3 so it picks up the mock
            service = BlockchainService()

            # Ensure CoinGecko path returns None to force Chainlink usage
            with patch.object(service, "_get_price_from_coingecko", return_value=None):
                price = await service.get_token_price(
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
                )

                assert price == 3000.0

    @pytest.mark.asyncio
    async def test_get_token_price_hardcoded_fallback(self, blockchain_service):
        """Test getting token price from hardcoded fallback."""
        # Mock CoinGecko and Chainlink to fail
        with patch.object(
            blockchain_service, "_get_price_from_coingecko", return_value=None
        ), patch.object(
            blockchain_service, "_get_price_from_chainlink", return_value=None
        ):
            price = await blockchain_service.get_token_price(
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
            )

            assert price == 3000.0  # Hardcoded WETH price

    @pytest.mark.asyncio
    async def test_get_token_price_not_found(self, blockchain_service):
        """Test getting token price for unknown token."""
        # Mock all price sources to fail
        with patch.object(
            blockchain_service, "_get_price_from_coingecko", return_value=None
        ), patch.object(
            blockchain_service, "_get_price_from_chainlink", return_value=None
        ):
            price = await blockchain_service.get_token_price("0xUnknownTokenAddress")

            assert price is None

    @pytest.mark.asyncio
    async def test_get_defi_positions(self, blockchain_service):
        """Test getting DeFi positions."""
        # Mock protocol position methods
        with patch.object(
            blockchain_service, "_get_aave_positions"
        ) as mock_aave, patch.object(
            blockchain_service, "_get_compound_positions"
        ) as mock_compound, patch.object(
            blockchain_service, "_get_staking_positions"
        ) as mock_staking:
            mock_aave.return_value = {
                "collaterals": [
                    {
                        "protocol": "aave",
                        "asset": "0x123",
                        "amount": 1.0,
                        "usd_value": 3000.0,
                    }
                ],
                "borrowings": [
                    {
                        "protocol": "aave",
                        "asset": "0x456",
                        "amount": 1000.0,
                        "usd_value": 1000.0,
                    }
                ],
                "health_scores": [{"protocol": "aave", "score": 0.85}],
            }

            mock_compound.return_value = {
                "collaterals": [
                    {
                        "protocol": "compound",
                        "asset": "0x789",
                        "amount": 0.1,
                        "usd_value": 4500.0,
                    }
                ],
                "borrowings": [
                    {
                        "protocol": "compound",
                        "asset": "0xabc",
                        "amount": 500.0,
                        "usd_value": 500.0,
                    }
                ],
                "health_scores": [{"protocol": "compound", "score": 0.92}],
            }

            mock_staking.return_value = [
                {
                    "protocol": "aave",
                    "asset": "0xdef",
                    "amount": 10.0,
                    "usd_value": 1000.0,
                    "apy": 0.08,
                }
            ]

            positions = await blockchain_service.get_defi_positions(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert len(positions["collaterals"]) == 2
            assert len(positions["borrowings"]) == 2
            assert len(positions["staked_positions"]) == 1
            assert len(positions["health_scores"]) == 2

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value(self, blockchain_service):
        """Test calculating portfolio value."""
        # Mock wallet balances and token prices
        with patch.object(
            blockchain_service, "get_wallet_balances"
        ) as mock_balances, patch.object(
            blockchain_service, "get_token_price"
        ) as mock_price:
            mock_balances.return_value = {
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": {
                    "balance_wei": 1000000000000000000,  # 1 ETH
                    "decimals": 18,
                },
                "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8": {
                    "balance_wei": 1000000000,  # 1000 USDC
                    "decimals": 6,
                },
            }

            mock_price.side_effect = [3000.0, 1.0]  # ETH price, USDC price

            portfolio_value = await blockchain_service.calculate_portfolio_value(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert portfolio_value["total_value"] == 4000.0  # 3000 + 1000
            assert len(portfolio_value["token_values"]) == 2
            assert (
                portfolio_value["token_values"][
                    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
                ]["value"]
                == 3000.0
            )
            assert (
                portfolio_value["token_values"][
                    "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8"
                ]["value"]
                == 1000.0
            )

    @pytest.mark.asyncio
    async def test_get_historical_data(self, blockchain_service):
        """Test getting historical data."""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        historical_data = await blockchain_service.get_historical_data(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", start_date, end_date, "daily"
        )

        assert len(historical_data) > 0
        assert all("timestamp" in point for point in historical_data)
        assert all("portfolio_value" in point for point in historical_data)
        assert all("collateral_value" in point for point in historical_data)
        assert all("borrowing_value" in point for point in historical_data)
        assert all("health_score" in point for point in historical_data)

    @pytest.mark.asyncio
    async def test_get_aave_positions(self, blockchain_service):
        """Test getting Aave positions."""
        positions = await blockchain_service._get_aave_positions(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert "collaterals" in positions
        assert "borrowings" in positions
        assert "health_scores" in positions
        assert len(positions["collaterals"]) > 0
        assert len(positions["borrowings"]) > 0
        assert len(positions["health_scores"]) > 0

    @pytest.mark.asyncio
    async def test_get_compound_positions(self, blockchain_service):
        """Test getting Compound positions."""
        positions = await blockchain_service._get_compound_positions(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert "collaterals" in positions
        assert "borrowings" in positions
        assert "health_scores" in positions
        assert len(positions["collaterals"]) > 0
        assert len(positions["borrowings"]) > 0
        assert len(positions["health_scores"]) > 0

    @pytest.mark.asyncio
    async def test_get_staking_positions(self, blockchain_service):
        """Test getting staking positions."""
        positions = await blockchain_service._get_staking_positions(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert len(positions) > 0
        assert all("protocol" in position for position in positions)
        assert all("asset" in position for position in positions)
        assert all("amount" in position for position in positions)
        assert all("usd_value" in position for position in positions)
        assert all("apy" in position for position in positions)

    def test_get_common_tokens(self, blockchain_service):
        """Test getting common token addresses."""
        tokens = blockchain_service._get_common_tokens()

        assert len(tokens) > 0
        assert all(token.startswith("0x") for token in tokens)
        assert "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" in tokens  # WETH
        assert "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8" in tokens  # USDC

    def test_get_erc20_abi(self, blockchain_service):
        """Test getting ERC20 ABI."""
        abi = blockchain_service._get_erc20_abi()

        assert len(abi) == 2
        assert any(func["name"] == "balanceOf" for func in abi)
        assert any(func["name"] == "decimals" for func in abi)

    def test_get_chainlink_abi(self, blockchain_service):
        """Test getting Chainlink ABI."""
        abi = blockchain_service._get_chainlink_abi()

        assert len(abi) == 1
        assert abi[0]["name"] == "latestRoundData"
        assert "outputs" in abi[0]

    def test_get_hardcoded_price(self, blockchain_service):
        """Test getting hardcoded prices."""
        # Test known tokens
        assert (
            blockchain_service._get_hardcoded_price(
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "USD"
            )
            == 3000.0
        )
        assert (
            blockchain_service._get_hardcoded_price(
                "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8", "USD"
            )
            == 1.0
        )
        assert (
            blockchain_service._get_hardcoded_price(
                "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", "USD"
            )
            == 45000.0
        )

        # Test unknown token
        assert blockchain_service._get_hardcoded_price("0xUnknownToken", "USD") is None

    def test_generate_mock_historical_data(self, blockchain_service):
        """Test generating mock historical data."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        data = blockchain_service._generate_mock_historical_data(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", start_date, end_date, "daily"
        )

        assert len(data) > 0
        assert all("timestamp" in point for point in data)
        assert all("portfolio_value" in point for point in data)
        assert all("collateral_value" in point for point in data)
        assert all("borrowing_value" in point for point in data)
        assert all("health_score" in point for point in data)

        # Check that values are reasonable
        for point in data:
            assert point["portfolio_value"] > 0
            assert point["collateral_value"] > 0
            assert point["borrowing_value"] >= 0
            assert 0 <= point["health_score"] <= 1

    def test_generate_mock_historical_data_weekly(self, blockchain_service):
        """Test generating mock historical data with weekly interval."""
        start_date = datetime.utcnow() - timedelta(weeks=4)
        end_date = datetime.utcnow()

        data = blockchain_service._generate_mock_historical_data(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", start_date, end_date, "weekly"
        )

        assert len(data) > 0
        assert len(data) <= 5  # Should be around 4-5 weeks

    def test_generate_mock_historical_data_monthly(self, blockchain_service):
        """Test generating mock historical data with monthly interval."""
        start_date = datetime.utcnow() - timedelta(days=90)
        end_date = datetime.utcnow()

        data = blockchain_service._generate_mock_historical_data(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            start_date,
            end_date,
            "monthly",
        )

        assert len(data) > 0
        assert len(data) <= 4  # Should be around 3-4 months

    @pytest.mark.asyncio
    async def test_error_handling_in_get_wallet_balances(self, blockchain_service):
        """Test error handling in get_wallet_balances."""
        blockchain_service.w3 = Mock()
        blockchain_service.w3.eth.contract.side_effect = Exception("Web3 error")

        balances = await blockchain_service.get_wallet_balances(
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        )

        assert balances == {}

    @pytest.mark.asyncio
    async def test_error_handling_in_get_token_price(self, blockchain_service):
        """Test error handling in get_token_price."""
        with patch.object(
            blockchain_service,
            "_get_price_from_coingecko",
            side_effect=Exception("API error"),
        ):
            price = await blockchain_service.get_token_price(
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
            )

            # Should fall back to hardcoded price
            assert price == 3000.0

    @pytest.mark.asyncio
    async def test_error_handling_in_get_defi_positions(self, blockchain_service):
        """Test error handling in get_defi_positions."""
        with patch.object(
            blockchain_service,
            "_get_aave_positions",
            side_effect=Exception("Aave error"),
        ):
            positions = await blockchain_service.get_defi_positions(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            # Should return empty positions on error
            assert positions["collaterals"] == []
            assert positions["borrowings"] == []
            assert positions["staked_positions"] == []
            assert positions["health_scores"] == []

    @pytest.mark.asyncio
    async def test_error_handling_in_calculate_portfolio_value(
        self, blockchain_service
    ):
        """Test error handling in calculate_portfolio_value."""
        with patch.object(
            blockchain_service,
            "get_wallet_balances",
            side_effect=Exception("Balance error"),
        ):
            portfolio_value = await blockchain_service.calculate_portfolio_value(
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            )

            assert portfolio_value["total_value"] == 0.0
            assert portfolio_value["token_values"] == {}

    def test_web3_connection_failure(self):
        """Test Web3 connection failure handling."""
        with patch("app.services.blockchain_service.settings") as mock_settings:
            mock_settings.ETHEREUM_RPC_URL = "http://invalid-url"

            service = BlockchainService()

            # Should handle connection failure gracefully
            assert service.w3 is None

    def test_web3_connection_success(self):
        """Test Web3 connection success."""
        with patch("app.services.blockchain_service.settings") as mock_settings, patch(
            "app.services.blockchain_service.Web3"
        ) as mock_web3_class:
            mock_settings.ETHEREUM_RPC_URL = "http://localhost:8545"
            mock_w3 = Mock()
            mock_w3.is_connected.return_value = True
            mock_web3_class.HTTPProvider.return_value = mock_w3

            service = BlockchainService()

            assert service.w3 is not None
            assert service.w3.is_connected()
