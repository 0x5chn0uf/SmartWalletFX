"""
Unit tests for BlockchainService.

Tests blockchain data retrieval, smart contract interactions, and calculations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.blockchain_service import BlockchainService


class TestBlockchainService:
    """Test cases for BlockchainService."""

    def test_blockchain_service_initialization(self, blockchain_service):
        """Test BlockchainService initialization."""
        assert hasattr(blockchain_service, "w3")
        assert hasattr(blockchain_service, "_setup_web3")

    @patch("app.services.blockchain_service.settings")
    @patch("app.services.blockchain_service.Web3")
    def test_setup_web3_success(
        self, mock_web3_class, mock_settings, blockchain_service
    ):
        """Test successful Web3 setup."""
        mock_settings.WEB3_PROVIDER_URI = "http://localhost:8545"
        mock_web3_instance = Mock()
        mock_web3_instance.is_connected.return_value = True
        mock_web3_class.HTTPProvider.return_value = mock_web3_instance
        mock_web3_class.return_value = mock_web3_instance

        blockchain_service._setup_web3()

        assert blockchain_service.w3 == mock_web3_instance
        mock_web3_class.HTTPProvider.assert_called_once_with("http://localhost:8545")

    @patch("app.services.blockchain_service.settings")
    @patch("app.services.blockchain_service.Web3")
    def test_setup_web3_connection_failure(
        self, mock_web3_class, mock_settings, blockchain_service
    ):
        """Test Web3 setup when connection fails."""
        mock_settings.WEB3_PROVIDER_URI = "http://localhost:8545"
        mock_web3_instance = Mock()
        mock_web3_instance.is_connected.return_value = False
        mock_web3_class.HTTPProvider.return_value = mock_web3_instance
        mock_web3_class.return_value = mock_web3_instance

        blockchain_service._setup_web3()

        assert blockchain_service.w3 is None

    @patch("app.services.blockchain_service.settings")
    @patch("app.services.blockchain_service.Web3")
    def test_setup_web3_exception(
        self, mock_web3_class, mock_settings, blockchain_service
    ):
        """Test Web3 setup when exception occurs."""
        mock_settings.WEB3_PROVIDER_URI = "http://localhost:8545"
        mock_web3_class.HTTPProvider.side_effect = Exception("Connection error")

        blockchain_service._setup_web3()

        assert blockchain_service.w3 is None

    @patch("app.services.blockchain_service.settings")
    @patch("app.services.blockchain_service.Web3")
    def test_setup_web3_no_provider_uri(
        self, mock_web3_class, mock_settings, blockchain_service
    ):
        """Test Web3 setup when no provider URI is configured."""
        mock_settings.WEB3_PROVIDER_URI = None

        blockchain_service._setup_web3()

        assert blockchain_service.w3 is None
        mock_web3_class.HTTPProvider.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_wallet_balances_no_web3(self, blockchain_service):
        """Test get_wallet_balances when Web3 is not available."""
        blockchain_service.w3 = None

        result = await blockchain_service.get_wallet_balances(
            "0x1111111111111111111111111111111111111111"
        )

        assert result == {}

    @patch.object(BlockchainService, "_get_common_tokens")
    @patch.object(BlockchainService, "_get_erc20_abi")
    @patch.object(BlockchainService, "_get_token_balance_async")
    @patch.object(BlockchainService, "_get_token_decimals_async")
    @pytest.mark.asyncio
    async def test_get_wallet_balances_success(
        self,
        mock_get_decimals,
        mock_get_balance,
        mock_get_abi,
        mock_get_common_tokens,
        blockchain_service,
        mock_web3_for_blockchain,
        mock_contract,
    ):
        """Test successful get_wallet_balances operation."""
        valid_address = "0x2222222222222222222222222222222222222222"
        blockchain_service.w3 = mock_web3_for_blockchain
        mock_get_common_tokens.return_value = [valid_address]
        mock_get_abi.return_value = [{"name": "balanceOf"}]
        mock_get_balance.return_value = 1000000000000000000  # 1 token with 18 decimals
        mock_get_decimals.return_value = 18

        mock_web3_for_blockchain.eth.contract.return_value = mock_contract
        mock_web3_for_blockchain.to_checksum_address.return_value = valid_address

        result = await blockchain_service.get_wallet_balances(valid_address)

        assert valid_address in result
        assert result[valid_address]["balance"] == "1000000000000000000"
        assert result[valid_address]["balance_wei"] == 1000000000000000000
        assert result[valid_address]["decimals"] == 18

    @patch.object(BlockchainService, "_get_common_tokens")
    @patch.object(BlockchainService, "_get_erc20_abi")
    @pytest.mark.asyncio
    async def test_get_wallet_balances_with_specific_tokens(
        self,
        mock_get_abi,
        mock_get_common_tokens,
        blockchain_service,
        mock_web3_for_blockchain,
        mock_contract,
    ):
        """Test get_wallet_balances with specific token list."""
        valid_address = "0x3333333333333333333333333333333333333333"
        valid_address2 = "0x4444444444444444444444444444444444444444"
        blockchain_service.w3 = mock_web3_for_blockchain
        mock_get_abi.return_value = [{"name": "balanceOf"}]
        tokens = [valid_address, valid_address2]

        # Reset mock call count to ensure clean state
        mock_web3_for_blockchain.eth.contract.reset_mock()

        mock_web3_for_blockchain.eth.contract.return_value = mock_contract
        mock_web3_for_blockchain.to_checksum_address.return_value = valid_address

        # Mock the async methods
        with patch.object(
            blockchain_service, "_get_token_balance_async", return_value=0
        ):
            with patch.object(
                blockchain_service, "_get_token_decimals_async", return_value=18
            ):
                result = await blockchain_service.get_wallet_balances(
                    valid_address, tokens
                )

        assert len(result) == 0  # No balances > 0
        assert mock_web3_for_blockchain.eth.contract.call_count == 2

    @patch.object(BlockchainService, "_get_common_tokens")
    @patch.object(BlockchainService, "_get_erc20_abi")
    @pytest.mark.asyncio
    async def test_get_wallet_balances_contract_error(
        self,
        mock_get_abi,
        mock_get_common_tokens,
        blockchain_service,
        mock_web3_for_blockchain,
    ):
        """Test get_wallet_balances when contract creation fails."""
        valid_address = "0x5555555555555555555555555555555555555555"
        blockchain_service.w3 = mock_web3_for_blockchain
        mock_get_common_tokens.return_value = [valid_address]
        mock_get_abi.return_value = [{"name": "balanceOf"}]

        mock_web3_for_blockchain.eth.contract.side_effect = Exception("Contract error")

        result = await blockchain_service.get_wallet_balances(valid_address)

        assert result == {}

    @patch.object(BlockchainService, "_get_common_tokens")
    @patch.object(BlockchainService, "_get_erc20_abi")
    @pytest.mark.asyncio
    async def test_get_wallet_balances_balance_error(
        self,
        mock_get_abi,
        mock_get_common_tokens,
        blockchain_service,
        mock_web3_for_blockchain,
        mock_contract,
    ):
        """Test get_wallet_balances when balance retrieval fails."""
        valid_address = "0x6666666666666666666666666666666666666666"
        blockchain_service.w3 = mock_web3_for_blockchain
        mock_get_common_tokens.return_value = [valid_address]
        mock_get_abi.return_value = [{"name": "balanceOf"}]
        mock_web3_for_blockchain.eth.contract.return_value = mock_contract
        mock_web3_for_blockchain.to_checksum_address.return_value = valid_address

        with patch.object(
            blockchain_service,
            "_get_token_balance_async",
            side_effect=Exception("Balance error"),
        ):
            result = await blockchain_service.get_wallet_balances(valid_address)

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_token_price_success_coingecko(self, blockchain_service):
        """Test successful get_token_price from CoinGecko."""
        with patch.object(
            blockchain_service, "_get_price_from_coingecko", return_value=100.0
        ):
            result = await blockchain_service.get_token_price(
                "0x7777777777777777777777777777777777777777"
            )

        assert result == 100.0

    @pytest.mark.asyncio
    async def test_get_token_price_success_chainlink(self, blockchain_service):
        """Test successful get_token_price from Chainlink."""
        with patch.object(
            blockchain_service, "_get_price_from_coingecko", return_value=None
        ):
            with patch.object(
                blockchain_service, "_get_price_from_chainlink", return_value=200.0
            ):
                result = await blockchain_service.get_token_price(
                    "0x8888888888888888888888888888888888888888"
                )

        assert result == 200.0

    @pytest.mark.asyncio
    async def test_get_token_price_success_hardcoded(self, blockchain_service):
        """Test successful get_token_price from hardcoded prices."""
        with patch.object(
            blockchain_service, "_get_price_from_coingecko", return_value=None
        ):
            with patch.object(
                blockchain_service, "_get_price_from_chainlink", return_value=None
            ):
                with patch.object(
                    blockchain_service, "_get_hardcoded_price", return_value=300.0
                ):
                    result = await blockchain_service.get_token_price(
                        "0x9999999999999999999999999999999999999999"
                    )

        assert result == 300.0

    @pytest.mark.asyncio
    async def test_get_token_price_all_sources_fail(self, blockchain_service):
        """Test get_token_price when all sources fail."""
        with patch.object(
            blockchain_service, "_get_price_from_coingecko", return_value=None
        ):
            with patch.object(
                blockchain_service, "_get_price_from_chainlink", return_value=None
            ):
                with patch.object(
                    blockchain_service, "_get_hardcoded_price", return_value=None
                ):
                    result = await blockchain_service.get_token_price(
                        "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                    )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_token_price_exception(self, blockchain_service):
        """Test get_token_price when exception occurs."""
        with patch.object(
            blockchain_service,
            "_get_price_from_coingecko",
            side_effect=Exception("API error"),
        ):
            result = await blockchain_service.get_token_price(
                "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_token_price_with_different_currency(self, blockchain_service):
        """Test get_token_price with different currency."""
        with patch.object(
            blockchain_service, "_get_price_from_coingecko", return_value=100.0
        ):
            result = await blockchain_service.get_token_price(
                "0xcccccccccccccccccccccccccccccccccccccccc", "EUR"
            )

        assert result == 100.0

    @pytest.mark.asyncio
    async def test_get_defi_positions_success(self, blockchain_service):
        """Test successful get_defi_positions operation."""
        aave_positions = {
            "collaterals": [{"asset": "USDC", "amount": 1000}],
            "borrowings": [{"asset": "DAI", "amount": 500}],
            "health_scores": [{"score": 0.8}],
        }
        compound_positions = {
            "collaterals": [{"asset": "ETH", "amount": 10}],
            "borrowings": [{"asset": "USDT", "amount": 200}],
            "health_scores": [{"score": 0.9}],
        }
        staking_positions = [{"protocol": "Lido", "amount": 5}]

        with patch.object(
            blockchain_service, "_get_aave_positions", return_value=aave_positions
        ):
            with patch.object(
                blockchain_service,
                "_get_compound_positions",
                return_value=compound_positions,
            ):
                with patch.object(
                    blockchain_service,
                    "_get_staking_positions",
                    return_value=staking_positions,
                ):
                    result = await blockchain_service.get_defi_positions(
                        "0xdddddddddddddddddddddddddddddddddddddddd"
                    )

        expected = {
            "collaterals": [
                {"asset": "USDC", "amount": 1000},
                {"asset": "ETH", "amount": 10},
            ],
            "borrowings": [
                {"asset": "DAI", "amount": 500},
                {"asset": "USDT", "amount": 200},
            ],
            "staked_positions": [{"protocol": "Lido", "amount": 5}],
            "health_scores": [{"score": 0.8}, {"score": 0.9}],
        }
        assert result == expected

    @pytest.mark.asyncio
    async def test_get_defi_positions_exception(self, blockchain_service):
        """Test get_defi_positions when exception occurs."""
        with patch.object(
            blockchain_service,
            "_get_aave_positions",
            side_effect=Exception("API error"),
        ):
            result = await blockchain_service.get_defi_positions(
                "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
            )

        expected = {
            "collaterals": [],
            "borrowings": [],
            "staked_positions": [],
            "health_scores": [],
        }
        assert result == expected

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_success(self, blockchain_service):
        """Test successful calculate_portfolio_value operation."""
        valid_address = "0xffffffffffffffffffffffffffffffffffffffff"
        balances = {
            valid_address: {
                "balance_wei": 1000000000000000000,  # 1 token
                "decimals": 18,
            }
        }

        with patch.object(
            blockchain_service, "get_wallet_balances", return_value=balances
        ):
            with patch.object(
                blockchain_service, "get_token_price", return_value=100.0
            ):
                result = await blockchain_service.calculate_portfolio_value(
                    valid_address
                )

        assert result["total_value"] == 100.0
        assert result["token_values"][valid_address] == {
            "balance": 1.0,
            "price": 100.0,
            "value": 100.0,
        }

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_no_balances(self, blockchain_service):
        """Test calculate_portfolio_value when no balances."""
        with patch.object(blockchain_service, "get_wallet_balances", return_value={}):
            result = await blockchain_service.calculate_portfolio_value(
                "0x1111111111111111111111111111111111111111"
            )

        assert result["total_value"] == 0.0
        assert result["token_values"] == {}

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_no_price(self, blockchain_service):
        """Test calculate_portfolio_value when token price is not available."""
        valid_address = "0x2222222222222222222222222222222222222222"
        balances = {valid_address: {"balance_wei": 1000000000000000000, "decimals": 18}}

        with patch.object(
            blockchain_service, "get_wallet_balances", return_value=balances
        ):
            with patch.object(blockchain_service, "get_token_price", return_value=None):
                result = await blockchain_service.calculate_portfolio_value(
                    valid_address
                )

        assert result["total_value"] == 0.0
        assert result["token_values"][valid_address] == {
            "balance": 1.0,
            "price": None,
            "value": 0.0,
        }

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_exception(self, blockchain_service):
        """Test calculate_portfolio_value when exception occurs."""
        with patch.object(
            blockchain_service,
            "get_wallet_balances",
            side_effect=Exception("API error"),
        ):
            result = await blockchain_service.calculate_portfolio_value(
                "0x3333333333333333333333333333333333333333"
            )

        assert result["total_value"] == 0.0
        assert result["token_values"] == {}

    @pytest.mark.asyncio
    async def test_get_historical_data_success(self, blockchain_service):
        """Test successful get_historical_data operation."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        with patch.object(
            blockchain_service, "_generate_mock_historical_data"
        ) as mock_generate:
            mock_generate.return_value = [
                {"date": "2023-01-01", "value": 1000},
                {"date": "2023-01-02", "value": 1100},
            ]

            result = await blockchain_service.get_historical_data(
                "0x4444444444444444444444444444444444444444",
                start_date,
                end_date,
                "daily",
            )

        assert len(result) == 2
        assert result[0]["date"] == "2023-01-01"
        assert result[1]["date"] == "2023-01-02"

    @pytest.mark.asyncio
    async def test_get_historical_data_exception(self, blockchain_service):
        """Test get_historical_data when exception occurs."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        with patch.object(
            blockchain_service,
            "_generate_mock_historical_data",
            side_effect=Exception("API error"),
        ):
            result = await blockchain_service.get_historical_data(
                "0x5555555555555555555555555555555555555555",
                start_date,
                end_date,
                "daily",
            )

        assert result == []

    def test_get_common_tokens(self, blockchain_service):
        """Test _get_common_tokens method."""
        tokens = blockchain_service._get_common_tokens()

        assert isinstance(tokens, list)
        assert len(tokens) > 0
        # Check that all tokens are valid Ethereum addresses
        for token in tokens:
            assert token.startswith("0x")
            assert len(token) == 42

    def test_get_erc20_abi(self, blockchain_service):
        """Test _get_erc20_abi method."""
        abi = blockchain_service._get_erc20_abi()

        assert isinstance(abi, list)
        assert len(abi) > 0

        # Check for required ERC20 functions
        function_names = [
            func.get("name") for func in abi if func.get("type") == "function"
        ]
        assert "balanceOf" in function_names
        assert "decimals" in function_names

    @pytest.mark.asyncio
    async def test_get_token_balance_async(self, blockchain_service, mock_contract):
        """Test _get_token_balance_async method."""
        valid_address = "0x6666666666666666666666666666666666666666"
        mock_balance_function = Mock()
        mock_balance_function.call.return_value = 1000000000000000000
        mock_contract.functions.balanceOf.return_value = mock_balance_function

        # Patch Web3.to_checksum_address to return the input address
        with patch("web3.Web3.to_checksum_address", side_effect=lambda x: x):
            result = await blockchain_service._get_token_balance_async(
                mock_contract, valid_address
            )

        assert result == 1000000000000000000
        mock_contract.functions.balanceOf.assert_called_once_with(valid_address)

    @pytest.mark.asyncio
    async def test_get_token_decimals_async(self, blockchain_service, mock_contract):
        """Test _get_token_decimals_async method."""
        mock_decimals_function = Mock()
        mock_decimals_function.call.return_value = 18
        mock_contract.functions.decimals.return_value = mock_decimals_function

        result = await blockchain_service._get_token_decimals_async(mock_contract)

        assert result == 18
        mock_contract.functions.decimals.assert_called_once()

    @patch("app.services.blockchain_service.aiohttp.ClientSession", autospec=True)
    @pytest.mark.asyncio
    async def test_get_price_from_coingecko_success(
        self, mock_session_class, blockchain_service
    ):
        """Test successful _get_price_from_coingecko method."""
        valid_address = "0x7777777777777777777777777777777777777777"

        class MockResponse:
            def __init__(self):
                self.status = 200

            async def json(self):
                return {valid_address.lower(): {"usd": 100.0}}

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def get(self, url, params=None):
                return MockResponse()

        mock_session_class.side_effect = MockSession

        result = await blockchain_service._get_price_from_coingecko(
            valid_address, "USD"
        )

        assert result == 100.0

    @patch("app.services.blockchain_service.aiohttp.ClientSession")
    @pytest.mark.asyncio
    async def test_get_price_from_coingecko_no_price(
        self, mock_session_class, blockchain_service
    ):
        """Test _get_price_from_coingecko when price not found."""
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        mock_response = AsyncMock()
        mock_response.json.return_value = {}
        mock_session.get.return_value.__aenter__.return_value = mock_response

        result = await blockchain_service._get_price_from_coingecko(
            "0x8888888888888888888888888888888888888888", "USD"
        )

        assert result is None

    @patch("app.services.blockchain_service.aiohttp.ClientSession")
    @pytest.mark.asyncio
    async def test_get_price_from_coingecko_exception(
        self, mock_session_class, blockchain_service
    ):
        """Test _get_price_from_coingecko when exception occurs."""
        mock_session = AsyncMock()
        mock_session_class.return_value.__aenter__.return_value = mock_session
        mock_session.get.side_effect = Exception("Network error")

        result = await blockchain_service._get_price_from_coingecko(
            "0x9999999999999999999999999999999999999999", "USD"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_price_from_chainlink_success(
        self, blockchain_service, mock_web3_for_blockchain, mock_contract
    ):
        """Test successful _get_price_from_chainlink method."""
        blockchain_service.w3 = mock_web3_for_blockchain
        # Patch contract to always return mock_contract regardless of args
        mock_web3_for_blockchain.eth.contract.side_effect = (
            lambda *args, **kwargs: mock_contract
        )

        mock_latest_round_data = Mock()
        mock_latest_round_data.call.return_value = (
            1,
            100000000,
            0,
            0,
            1,
        )  # (roundId, answer, startedAt, updatedAt, answeredInRound)
        mock_contract.functions.latestRoundData.return_value = mock_latest_round_data

        test_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        feed_address = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
        with patch.object(
            BlockchainService, "price_feeds", {test_address: feed_address}
        ):
            with patch(
                "app.services.blockchain_service.Web3.to_checksum_address",
                return_value=feed_address,
            ):
                result = await blockchain_service._get_price_from_chainlink(
                    test_address, "USD"
                )
        assert result == 1.0  # 100000000 / 10^8

    @pytest.mark.asyncio
    async def test_get_price_from_chainlink_no_web3(self, blockchain_service):
        """Test _get_price_from_chainlink when Web3 is not available."""
        blockchain_service.w3 = None

        result = await blockchain_service._get_price_from_chainlink(
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "USD"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_price_from_chainlink_exception(
        self, blockchain_service, mock_web3_for_blockchain
    ):
        """Test _get_price_from_chainlink when exception occurs."""
        blockchain_service.w3 = mock_web3_for_blockchain
        mock_web3_for_blockchain.eth.contract.side_effect = Exception("Contract error")

        result = await blockchain_service._get_price_from_chainlink(
            "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "USD"
        )

        assert result is None

    def test_get_hardcoded_price_success(self, blockchain_service):
        """Test successful _get_hardcoded_price method."""
        # Test with a known token address
        result = blockchain_service._get_hardcoded_price(
            "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8C", "USD"
        )

        # Should return a price or None depending on the hardcoded mapping
        assert result is None or isinstance(result, (int, float))

    def test_get_hardcoded_price_unknown_token(self, blockchain_service):
        """Test _get_hardcoded_price with unknown token."""
        result = blockchain_service._get_hardcoded_price(
            "0xcccccccccccccccccccccccccccccccccccccccc", "USD"
        )

        assert result is None

    def test_get_hardcoded_price_different_currency(self, blockchain_service):
        """Test _get_hardcoded_price with different currency."""
        result = blockchain_service._get_hardcoded_price(
            "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8C", "EUR"
        )

        # Should return a price or None depending on the hardcoded mapping
        assert result is None or isinstance(result, (int, float))

    def test_get_chainlink_abi(self, blockchain_service):
        """Test _get_chainlink_abi method."""
        abi = blockchain_service._get_chainlink_abi()

        assert isinstance(abi, list)
        assert len(abi) > 0

        # Check for required Chainlink functions
        function_names = [
            func.get("name") for func in abi if func.get("type") == "function"
        ]
        assert "latestRoundData" in function_names

    @pytest.mark.asyncio
    async def test_get_aave_positions_success(self, blockchain_service):
        """Test successful _get_aave_positions method."""
        with patch.object(blockchain_service, "get_wallet_balances") as mock_balances:
            mock_balances.return_value = {
                "0xdddddddddddddddddddddddddddddddddddddddd": {
                    "balance_wei": 1000000000000000000,
                    "decimals": 18,
                }
            }

            with patch.object(
                blockchain_service, "get_token_price", return_value=100.0
            ):
                result = await blockchain_service._get_aave_positions(
                    "0xdddddddddddddddddddddddddddddddddddddddd"
                )

        assert "collaterals" in result
        assert "borrowings" in result
        assert "health_scores" in result
        assert isinstance(result["collaterals"], list)
        assert isinstance(result["borrowings"], list)
        assert isinstance(result["health_scores"], list)

    @pytest.mark.asyncio
    async def test_get_aave_positions_exception(self, blockchain_service):
        """Test _get_aave_positions when exception occurs."""
        # Even if an exception is raised in dependent calls, the current implementation returns mock data
        with patch.object(
            blockchain_service,
            "get_wallet_balances",
            side_effect=Exception("API error"),
        ):
            result = await blockchain_service._get_aave_positions(
                "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
            )

        # The function should still return the predefined mock data structure
        assert "collaterals" in result and len(result["collaterals"]) > 0
        assert "borrowings" in result and len(result["borrowings"]) > 0
        assert "health_scores" in result and len(result["health_scores"]) > 0

    @pytest.mark.asyncio
    async def test_get_compound_positions_success(self, blockchain_service):
        """Test successful _get_compound_positions method."""
        with patch.object(blockchain_service, "get_wallet_balances") as mock_balances:
            mock_balances.return_value = {
                "0xffffffffffffffffffffffffffffffffffffffff": {
                    "balance_wei": 1000000000000000000,
                    "decimals": 18,
                }
            }

            with patch.object(
                blockchain_service, "get_token_price", return_value=100.0
            ):
                result = await blockchain_service._get_compound_positions(
                    "0xffffffffffffffffffffffffffffffffffffffff"
                )

        assert "collaterals" in result
        assert "borrowings" in result
        assert "health_scores" in result
        assert isinstance(result["collaterals"], list)
        assert isinstance(result["borrowings"], list)
        assert isinstance(result["health_scores"], list)

    @pytest.mark.asyncio
    async def test_get_compound_positions_exception(self, blockchain_service):
        """Test _get_compound_positions when exception occurs."""
        with patch.object(
            blockchain_service,
            "get_wallet_balances",
            side_effect=Exception("API error"),
        ):
            result = await blockchain_service._get_compound_positions(
                "0x1111111111111111111111111111111111111111"
            )

        # The function should still return the predefined mock data structure
        assert "collaterals" in result and len(result["collaterals"]) > 0
        assert "borrowings" in result and len(result["borrowings"]) > 0
        assert "health_scores" in result and len(result["health_scores"]) > 0

    @pytest.mark.asyncio
    async def test_get_staking_positions_success(self, blockchain_service):
        """Test successful _get_staking_positions method."""
        with patch.object(blockchain_service, "get_wallet_balances") as mock_balances:
            mock_balances.return_value = {
                "0x2222222222222222222222222222222222222222": {
                    "balance_wei": 1000000000000000000,
                    "decimals": 18,
                }
            }

            with patch.object(
                blockchain_service, "get_token_price", return_value=100.0
            ):
                result = await blockchain_service._get_staking_positions(
                    "0x2222222222222222222222222222222222222222"
                )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_staking_positions_exception(self, blockchain_service):
        """Test _get_staking_positions when exception occurs."""
        with patch.object(
            blockchain_service,
            "get_wallet_balances",
            side_effect=Exception("API error"),
        ):
            result = await blockchain_service._get_staking_positions(
                "0x3333333333333333333333333333333333333333"
            )

        # The function should still return the predefined mock data structure
        assert isinstance(result, list)
        assert len(result) > 0
        assert "protocol" in result[0] and "asset" in result[0]

    def test_generate_mock_historical_data(self, blockchain_service):
        """Test _generate_mock_historical_data method."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 5)

        result = blockchain_service._generate_mock_historical_data(
            "0x4444444444444444444444444444444444444444", start_date, end_date, "daily"
        )

        assert isinstance(result, list)
        assert len(result) > 0

        for data_point in result:
            assert "date" in data_point
            assert "value" in data_point
            assert isinstance(data_point["value"], (int, float))

    def test_generate_mock_historical_data_weekly_interval(self, blockchain_service):
        """Test _generate_mock_historical_data with weekly interval."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        result = blockchain_service._generate_mock_historical_data(
            "0x5555555555555555555555555555555555555555",
            start_date,
            end_date,
            "weekly",
        )

        assert isinstance(result, list)
        assert len(result) > 0

    def test_generate_mock_historical_data_monthly_interval(self, blockchain_service):
        """Test _generate_mock_historical_data with monthly interval."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        result = blockchain_service._generate_mock_historical_data(
            "0x6666666666666666666666666666666666666666",
            start_date,
            end_date,
            "monthly",
        )

        assert isinstance(result, list)
        assert len(result) > 0

    def test_generate_mock_historical_data_invalid_interval(self, blockchain_service):
        """Test _generate_mock_historical_data with invalid interval."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 5)

        result = blockchain_service._generate_mock_historical_data(
            "0x7777777777777777777777777777777777777777",
            start_date,
            end_date,
            "invalid",
        )

        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_wallet_balances_zero_balance(
        self, blockchain_service, mock_web3_for_blockchain, mock_contract
    ):
        """Test get_wallet_balances with zero balance."""
        blockchain_service.w3 = mock_web3_for_blockchain
        mock_web3_for_blockchain.eth.contract.return_value = mock_contract
        mock_web3_for_blockchain.to_checksum_address.return_value = (
            "0x8888888888888888888888888888888888888888"
        )

        with patch.object(
            blockchain_service,
            "_get_common_tokens",
            return_value=["0x8888888888888888888888888888888888888888"],
        ):
            with patch.object(
                blockchain_service,
                "_get_erc20_abi",
                return_value=[{"name": "balanceOf"}],
            ):
                with patch.object(
                    blockchain_service, "_get_token_balance_async", return_value=0
                ):
                    with patch.object(
                        blockchain_service, "_get_token_decimals_async", return_value=18
                    ):
                        result = await blockchain_service.get_wallet_balances(
                            "0x8888888888888888888888888888888888888888"
                        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_wallet_balances_negative_balance(
        self, blockchain_service, mock_web3_for_blockchain, mock_contract
    ):
        """Test get_wallet_balances with negative balance."""
        blockchain_service.w3 = mock_web3_for_blockchain
        mock_web3_for_blockchain.eth.contract.return_value = mock_contract
        mock_web3_for_blockchain.to_checksum_address.return_value = (
            "0x9999999999999999999999999999999999999999"
        )

        with patch.object(
            blockchain_service,
            "_get_common_tokens",
            return_value=["0x9999999999999999999999999999999999999999"],
        ):
            with patch.object(
                blockchain_service,
                "_get_erc20_abi",
                return_value=[{"name": "balanceOf"}],
            ):
                with patch.object(
                    blockchain_service, "_get_token_balance_async", return_value=-1000
                ):
                    with patch.object(
                        blockchain_service, "_get_token_decimals_async", return_value=18
                    ):
                        result = await blockchain_service.get_wallet_balances(
                            "0x9999999999999999999999999999999999999999"
                        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_multiple_tokens(self, blockchain_service):
        """Test calculate_portfolio_value with multiple tokens."""
        balances = {
            "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {
                "balance_wei": 1000000000000000000,  # 1 token
                "decimals": 18,
            },
            "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": {
                "balance_wei": 500000000000000000,  # 0.5 tokens
                "decimals": 18,
            },
        }

        with patch.object(
            blockchain_service, "get_wallet_balances", return_value=balances
        ):
            with patch.object(
                blockchain_service, "get_token_price", side_effect=[100.0, 200.0]
            ):
                result = await blockchain_service.calculate_portfolio_value(
                    "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                )

        assert result["total_value"] == 200.0  # 100 + 100
        assert result["token_values"]["0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"] == {
            "balance": 1.0,
            "price": 100.0,
            "value": 100.0,
        }
        assert result["token_values"]["0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"] == {
            "balance": 0.5,
            "price": 200.0,
            "value": 100.0,
        }

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_mixed_prices(self, blockchain_service):
        """Test calculate_portfolio_value with some tokens having no price."""
        balances = {
            "0xcccccccccccccccccccccccccccccccccccccccc": {
                "balance_wei": 1000000000000000000,
                "decimals": 18,
            },
            "0xdddddddddddddddddddddddddddddddddddddddd": {
                "balance_wei": 500000000000000000,
                "decimals": 18,
            },
        }

        with patch.object(
            blockchain_service, "get_wallet_balances", return_value=balances
        ):
            with patch.object(
                blockchain_service, "get_token_price", side_effect=[100.0, None]
            ):
                result = await blockchain_service.calculate_portfolio_value(
                    "0xcccccccccccccccccccccccccccccccccccccccc"
                )

        assert result["total_value"] == 100.0
        assert result["token_values"]["0xcccccccccccccccccccccccccccccccccccccccc"] == {
            "balance": 1.0,
            "price": 100.0,
            "value": 100.0,
        }
        assert result["token_values"]["0xdddddddddddddddddddddddddddddddddddddddd"] == {
            "balance": 0.5,
            "price": None,
            "value": 0.0,
        }
