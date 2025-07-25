"""Unit tests for TokenUsecase."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.schemas.token import TokenCreate, TokenResponse
from app.usecase.token_usecase import TokenUsecase


class TestTokenUsecase:
    """Test TokenUsecase class."""

    @pytest.mark.unit
    def test_init(self, token_usecase_with_di):
        """Test TokenUsecase initialization."""
        usecase = token_usecase_with_di

        assert usecase._TokenUsecase__token_repo is not None
        assert usecase._TokenUsecase__config_service is not None
        assert usecase._TokenUsecase__audit is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_success(self, token_usecase_with_di):
        """Test successful token creation."""
        usecase = token_usecase_with_di

        # Create input
        token_create = TokenCreate(
            address="0x1234567890123456789012345678901234567890",
            symbol="TEST",
            name="Test Token",
            decimals=18,
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenResponse(
            id=created_id,
            address=token_create.address,
            symbol=token_create.symbol,
            name=token_create.name,
            decimals=token_create.decimals,
        )

        usecase._TokenUsecase__token_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token(token_create)

        # Verify
        assert result == expected_response
        assert result.id == created_id
        assert result.address == token_create.address
        assert result.symbol == token_create.symbol
        assert result.name == token_create.name
        assert result.decimals == token_create.decimals

        # Verify repository was called with correct data
        usecase._TokenUsecase__token_repo.create.assert_called_once_with(token_create)

        # Verify audit logging
        usecase._TokenUsecase__audit.info.assert_any_call(
            "token_usecase_create_started",
            token_symbol="TEST",
        )
        usecase._TokenUsecase__audit.info.assert_any_call(
            "token_usecase_create_success",
            token_id=str(created_id),
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_with_default_decimals(self, token_usecase_with_di):
        """Test token creation with default decimals."""
        usecase = token_usecase_with_di

        # Create input with default decimals
        token_create = TokenCreate(
            address="0xabcdef1234567890123456789012345678901234",
            symbol="ETH",
            name="Ethereum",
            # decimals not specified, should default to 18
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenResponse(
            id=created_id,
            address=token_create.address,
            symbol=token_create.symbol,
            name=token_create.name,
            decimals=18,  # default value
        )

        usecase._TokenUsecase__token_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token(token_create)

        # Verify
        assert result == expected_response
        assert result.decimals == 18

        # Verify audit logging
        usecase._TokenUsecase__audit.info.assert_any_call(
            "token_usecase_create_started",
            token_symbol="ETH",
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_with_custom_decimals(self, token_usecase_with_di):
        """Test token creation with custom decimals."""
        usecase = token_usecase_with_di

        # Create input with custom decimals
        token_create = TokenCreate(
            address="0xabcdef1234567890123456789012345678901234",
            symbol="USDC",
            name="USD Coin",
            decimals=6,  # Custom decimals
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenResponse(
            id=created_id,
            address=token_create.address,
            symbol=token_create.symbol,
            name=token_create.name,
            decimals=6,
        )

        usecase._TokenUsecase__token_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token(token_create)

        # Verify
        assert result == expected_response
        assert result.decimals == 6

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_zero_decimals(self, token_usecase_with_di):
        """Test token creation with zero decimals."""
        usecase = token_usecase_with_di

        # Create input with zero decimals
        token_create = TokenCreate(
            address="0xabcdef1234567890123456789012345678901234",
            symbol="NFT",
            name="Non-Fungible Token",
            decimals=0,
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenResponse(
            id=created_id,
            address=token_create.address,
            symbol=token_create.symbol,
            name=token_create.name,
            decimals=0,
        )

        usecase._TokenUsecase__token_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token(token_create)

        # Verify
        assert result == expected_response
        assert result.decimals == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_without_symbol_attribute(self, token_usecase_with_di):
        """Test token creation when input doesn't have symbol attribute."""
        usecase = token_usecase_with_di

        # Create mock input without symbol attribute
        token_create = Mock(spec=["address", "name", "decimals"])
        token_create.address = "0x1234567890123456789012345678901234567890"
        token_create.name = "Test Token"
        token_create.decimals = 18

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenResponse(
            id=created_id,
            address=token_create.address,
            symbol="UNKNOWN",
            name=token_create.name,
            decimals=token_create.decimals,
        )

        usecase._TokenUsecase__token_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token(token_create)

        # Verify
        assert result == expected_response

        # Verify audit logging with None for symbol
        usecase._TokenUsecase__audit.info.assert_any_call(
            "token_usecase_create_started",
            token_symbol=None,
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_long_name(self, token_usecase_with_di):
        """Test token creation with long name."""
        usecase = token_usecase_with_di

        # Create input with long name
        long_name = "A" * 100  # Very long name
        token_create = TokenCreate(
            address="0x1234567890123456789012345678901234567890",
            symbol="LONG",
            name=long_name,
            decimals=18,
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenResponse(
            id=created_id,
            address=token_create.address,
            symbol=token_create.symbol,
            name=long_name,
            decimals=token_create.decimals,
        )

        usecase._TokenUsecase__token_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token(token_create)

        # Verify
        assert result == expected_response
        assert result.name == long_name

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_special_characters(self, token_usecase_with_di):
        """Test token creation with special characters."""
        usecase = token_usecase_with_di

        # Create input with special characters
        token_create = TokenCreate(
            address="0x1234567890123456789012345678901234567890",
            symbol="ÜNÏ",
            name="Ünïcødé Tøkën",
            decimals=18,
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenResponse(
            id=created_id,
            address=token_create.address,
            symbol=token_create.symbol,
            name=token_create.name,
            decimals=token_create.decimals,
        )

        usecase._TokenUsecase__token_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token(token_create)

        # Verify
        assert result == expected_response
        assert result.symbol == "ÜNÏ"
        assert result.name == "Ünïcødé Tøkën"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_repository_exception(self, token_usecase_with_di):
        """Test token creation with repository exception."""
        usecase = token_usecase_with_di

        # Create input
        token_create = TokenCreate(
            address="0x1234567890123456789012345678901234567890",
            symbol="ERR",
            name="Error Token",
            decimals=18,
        )

        # Mock repository exception
        usecase._TokenUsecase__token_repo.create = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database connection failed"):
            await usecase.create_token(token_create)

        # Verify audit logging
        usecase._TokenUsecase__audit.info.assert_any_call(
            "token_usecase_create_started",
            token_symbol="ERR",
        )
        usecase._TokenUsecase__audit.error.assert_called_once_with(
            "token_usecase_create_failed",
            error="Database connection failed",
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_validation_error(self, token_usecase_with_di):
        """Test token creation with validation error."""
        usecase = token_usecase_with_di

        # Create input
        token_create = TokenCreate(
            address="invalid_address", symbol="TEST", name="Test Token", decimals=18
        )

        # Mock repository validation error
        usecase._TokenUsecase__token_repo.create = AsyncMock(
            side_effect=ValueError("Invalid token address")
        )

        # Execute and verify exception
        with pytest.raises(ValueError, match="Invalid token address"):
            await usecase.create_token(token_create)

        # Verify audit logging
        usecase._TokenUsecase__audit.error.assert_called_once_with(
            "token_usecase_create_failed",
            error="Invalid token address",
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_result_without_id(self, token_usecase_with_di):
        """Test token creation when result doesn't have id attribute."""
        usecase = token_usecase_with_di

        # Create input
        token_create = TokenCreate(
            address="0x1234567890123456789012345678901234567890",
            symbol="TEST",
            name="Test Token",
            decimals=18,
        )

        # Mock repository response without id attribute
        mock_response = Mock(spec=["address", "symbol", "name", "decimals"])
        mock_response.address = token_create.address
        mock_response.symbol = token_create.symbol
        mock_response.name = token_create.name
        mock_response.decimals = token_create.decimals

        usecase._TokenUsecase__token_repo.create = AsyncMock(return_value=mock_response)

        # Execute
        result = await usecase.create_token(token_create)

        # Verify
        assert result == mock_response
        assert result.address == token_create.address
        assert result.symbol == token_create.symbol
        assert result.name == token_create.name
        assert result.decimals == token_create.decimals

        # Verify audit logging with None for id
        usecase._TokenUsecase__audit.info.assert_any_call(
            "token_usecase_create_success",
            token_id=None,
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_duplicate_address(self, token_usecase_with_di):
        """Test token creation with duplicate address."""
        usecase = token_usecase_with_di

        # Create input with duplicate address
        token_create = TokenCreate(
            address="0x1234567890123456789012345678901234567890",
            symbol="DUP",
            name="Duplicate Token",
            decimals=18,
        )

        # Mock repository duplicate error
        usecase._TokenUsecase__token_repo.create = AsyncMock(
            side_effect=Exception("Token with address already exists")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Token with address already exists"):
            await usecase.create_token(token_create)

        # Verify audit logging
        usecase._TokenUsecase__audit.error.assert_called_once_with(
            "token_usecase_create_failed",
            error="Token with address already exists",
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_multiple_calls(self, token_usecase_with_di):
        """Test multiple token creations."""
        usecase = token_usecase_with_di

        # First call
        token_create_1 = TokenCreate(
            address="0x1111111111111111111111111111111111111111",
            symbol="TOK1",
            name="Token 1",
            decimals=18,
        )
        expected_response_1 = TokenResponse(
            id=uuid.uuid4(),
            address=token_create_1.address,
            symbol=token_create_1.symbol,
            name=token_create_1.name,
            decimals=token_create_1.decimals,
        )

        # Second call
        token_create_2 = TokenCreate(
            address="0x2222222222222222222222222222222222222222",
            symbol="TOK2",
            name="Token 2",
            decimals=6,
        )
        expected_response_2 = TokenResponse(
            id=uuid.uuid4(),
            address=token_create_2.address,
            symbol=token_create_2.symbol,
            name=token_create_2.name,
            decimals=token_create_2.decimals,
        )

        # Mock repository responses
        usecase._TokenUsecase__token_repo.create = AsyncMock(
            side_effect=[expected_response_1, expected_response_2]
        )

        # Execute
        result_1 = await usecase.create_token(token_create_1)
        result_2 = await usecase.create_token(token_create_2)

        # Verify
        assert result_1 == expected_response_1
        assert result_2 == expected_response_2

        # Verify repository was called twice
        assert usecase._TokenUsecase__token_repo.create.call_count == 2

        # Verify audit logging was called for both
        assert (
            usecase._TokenUsecase__audit.info.call_count == 4
        )  # 2 started + 2 success

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_concurrent_calls(self, token_usecase_with_di):
        """Test concurrent token creations."""
        usecase = token_usecase_with_di

        # Create multiple inputs
        token_creates = [
            TokenCreate(
                address=f"0x{i:040x}", symbol=f"TOK{i}", name=f"Token {i}", decimals=18
            )
            for i in range(1, 4)
        ]

        # Mock repository responses
        expected_responses = [
            TokenResponse(
                id=uuid.uuid4(),
                address=tc.address,
                symbol=tc.symbol,
                name=tc.name,
                decimals=tc.decimals,
            )
            for tc in token_creates
        ]

        usecase._TokenUsecase__token_repo.create = AsyncMock(
            side_effect=expected_responses
        )

        # Execute concurrently
        import asyncio

        results = await asyncio.gather(
            *[usecase.create_token(tc) for tc in token_creates]
        )

        # Verify
        assert len(results) == 3
        for result, expected in zip(results, expected_responses):
            assert result == expected

        # Verify repository was called for each
        assert usecase._TokenUsecase__token_repo.create.call_count == 3
