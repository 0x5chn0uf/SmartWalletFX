"""Unit tests for TokenPriceUsecase."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.schemas.token_price import TokenPriceCreate, TokenPriceResponse
from app.usecase.token_price_usecase import TokenPriceUsecase


class TestTokenPriceUsecase:
    """Test TokenPriceUsecase class."""

    @pytest.mark.unit
    def test_init(self, token_price_usecase_with_di):
        """Test TokenPriceUsecase initialization."""
        usecase = token_price_usecase_with_di

        assert usecase._TokenPriceUsecase__token_price_repo is not None
        assert usecase._TokenPriceUsecase__config_service is not None
        assert usecase._TokenPriceUsecase__audit is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_success(self, token_price_usecase_with_di):
        """Test successful token price creation."""
        usecase = token_price_usecase_with_di
        token_id = uuid.uuid4()
        price_usd = 1500.50

        # Create input
        token_price_create = TokenPriceCreate(token_id=token_id, price_usd=price_usd)

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenPriceResponse(
            id=created_id, token_id=token_id, price_usd=price_usd
        )

        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_price(token_price_create)

        # Verify
        assert result == expected_response
        assert result.id == created_id
        assert result.token_id == token_id
        assert result.price_usd == price_usd

        # Verify repository was called with correct data
        usecase._TokenPriceUsecase__token_price_repo.create.assert_called_once_with(
            token_price_create
        )

        # Verify audit logging
        usecase._TokenPriceUsecase__audit.info.assert_any_call(
            "token_price_usecase_create_started",
            token_symbol=None,  # TokenPriceCreate doesn't have symbol
        )
        usecase._TokenPriceUsecase__audit.info.assert_any_call(
            "token_price_usecase_create_success",
            token_price_id=str(created_id),
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_with_symbol_attribute(
        self, token_price_usecase_with_di
    ):
        """Test token price creation with symbol attribute using mock."""
        usecase = token_price_usecase_with_di
        token_id = uuid.uuid4()
        price_usd = 25.75

        # Create mock input with symbol attribute
        token_price_create = Mock()
        token_price_create.token_id = token_id
        token_price_create.price_usd = price_usd
        token_price_create.symbol = "ETH"

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenPriceResponse(
            id=created_id, token_id=token_id, price_usd=price_usd
        )

        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_price(token_price_create)

        # Verify
        assert result == expected_response

        # Verify audit logging includes symbol
        usecase._TokenPriceUsecase__audit.info.assert_any_call(
            "token_price_usecase_create_started",
            token_symbol="ETH",
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_zero_price(self, token_price_usecase_with_di):
        """Test token price creation with zero price."""
        usecase = token_price_usecase_with_di
        token_id = uuid.uuid4()
        price_usd = 0.0

        # Create input
        token_price_create = TokenPriceCreate(token_id=token_id, price_usd=price_usd)

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenPriceResponse(
            id=created_id, token_id=token_id, price_usd=price_usd
        )

        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_price(token_price_create)

        # Verify
        assert result == expected_response
        assert result.price_usd == 0.0

        # Verify audit logging
        usecase._TokenPriceUsecase__audit.info.assert_any_call(
            "token_price_usecase_create_success",
            token_price_id=str(created_id),
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_very_small_price(
        self, token_price_usecase_with_di
    ):
        """Test token price creation with very small price."""
        usecase = token_price_usecase_with_di
        token_id = uuid.uuid4()
        price_usd = 0.00000001  # Very small price

        # Create input
        token_price_create = TokenPriceCreate(token_id=token_id, price_usd=price_usd)

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenPriceResponse(
            id=created_id, token_id=token_id, price_usd=price_usd
        )

        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_price(token_price_create)

        # Verify
        assert result == expected_response
        assert result.price_usd == price_usd

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_very_large_price(
        self, token_price_usecase_with_di
    ):
        """Test token price creation with very large price."""
        usecase = token_price_usecase_with_di
        token_id = uuid.uuid4()
        price_usd = 999999999.99  # Very large price

        # Create input
        token_price_create = TokenPriceCreate(token_id=token_id, price_usd=price_usd)

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenPriceResponse(
            id=created_id, token_id=token_id, price_usd=price_usd
        )

        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_price(token_price_create)

        # Verify
        assert result == expected_response
        assert result.price_usd == price_usd

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_repository_exception(
        self, token_price_usecase_with_di
    ):
        """Test token price creation with repository exception."""
        usecase = token_price_usecase_with_di
        token_id = uuid.uuid4()
        price_usd = 100.0

        # Create input
        token_price_create = TokenPriceCreate(token_id=token_id, price_usd=price_usd)

        # Mock repository exception
        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database connection failed"):
            await usecase.create_token_price(token_price_create)

        # Verify audit logging
        usecase._TokenPriceUsecase__audit.info.assert_any_call(
            "token_price_usecase_create_started",
            token_symbol=None,
        )
        usecase._TokenPriceUsecase__audit.error.assert_called_once_with(
            "token_price_usecase_create_failed",
            error="Database connection failed",
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_validation_error(
        self, token_price_usecase_with_di
    ):
        """Test token price creation with validation error."""
        usecase = token_price_usecase_with_di
        token_id = uuid.uuid4()
        price_usd = 50.0

        # Create input
        token_price_create = TokenPriceCreate(token_id=token_id, price_usd=price_usd)

        # Mock repository validation error
        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            side_effect=ValueError("Invalid token ID")
        )

        # Execute and verify exception
        with pytest.raises(ValueError, match="Invalid token ID"):
            await usecase.create_token_price(token_price_create)

        # Verify audit logging
        usecase._TokenPriceUsecase__audit.error.assert_called_once_with(
            "token_price_usecase_create_failed",
            error="Invalid token ID",
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_result_without_id(
        self, token_price_usecase_with_di
    ):
        """Test token price creation when result doesn't have id attribute."""
        usecase = token_price_usecase_with_di
        token_id = uuid.uuid4()
        price_usd = 42.0

        # Create input
        token_price_create = TokenPriceCreate(token_id=token_id, price_usd=price_usd)

        # Mock repository response without id attribute
        mock_response = Mock(
            spec=["token_id", "price_usd"]
        )  # Specify only these attributes
        mock_response.token_id = token_id
        mock_response.price_usd = price_usd

        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            return_value=mock_response
        )

        # Execute
        result = await usecase.create_token_price(token_price_create)

        # Verify
        assert result == mock_response
        assert result.token_id == token_id
        assert result.price_usd == price_usd

        # Verify audit logging with None for id
        usecase._TokenPriceUsecase__audit.info.assert_any_call(
            "token_price_usecase_create_success",
            token_price_id=None,
        )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_negative_price(self, token_price_usecase_with_di):
        """Test token price creation with negative price."""
        usecase = token_price_usecase_with_di
        token_id = uuid.uuid4()
        price_usd = -10.5  # Negative price

        # Create input
        token_price_create = TokenPriceCreate(token_id=token_id, price_usd=price_usd)

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenPriceResponse(
            id=created_id, token_id=token_id, price_usd=price_usd
        )

        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_price(token_price_create)

        # Verify
        assert result == expected_response
        assert result.price_usd == price_usd  # Should handle negative prices

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_multiple_calls(self, token_price_usecase_with_di):
        """Test multiple token price creations."""
        usecase = token_price_usecase_with_di

        # First call
        token_id_1 = uuid.uuid4()
        price_usd_1 = 100.0
        token_price_create_1 = TokenPriceCreate(
            token_id=token_id_1, price_usd=price_usd_1
        )
        expected_response_1 = TokenPriceResponse(
            id=uuid.uuid4(), token_id=token_id_1, price_usd=price_usd_1
        )

        # Second call
        token_id_2 = uuid.uuid4()
        price_usd_2 = 200.0
        token_price_create_2 = TokenPriceCreate(
            token_id=token_id_2, price_usd=price_usd_2
        )
        expected_response_2 = TokenPriceResponse(
            id=uuid.uuid4(), token_id=token_id_2, price_usd=price_usd_2
        )

        # Mock repository responses
        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            side_effect=[expected_response_1, expected_response_2]
        )

        # Execute
        result_1 = await usecase.create_token_price(token_price_create_1)
        result_2 = await usecase.create_token_price(token_price_create_2)

        # Verify
        assert result_1 == expected_response_1
        assert result_2 == expected_response_2

        # Verify repository was called twice
        assert usecase._TokenPriceUsecase__token_price_repo.create.call_count == 2

        # Verify audit logging was called for both
        assert (
            usecase._TokenPriceUsecase__audit.info.call_count == 4
        )  # 2 started + 2 success

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_token_price_concurrent_calls(
        self, token_price_usecase_with_di
    ):
        """Test concurrent token price creations."""
        usecase = token_price_usecase_with_di

        # Create multiple inputs
        token_ids = [uuid.uuid4() for _ in range(3)]
        prices = [100.0, 200.0, 300.0]
        token_price_creates = [
            TokenPriceCreate(token_id=token_id, price_usd=price)
            for token_id, price in zip(token_ids, prices)
        ]

        # Mock repository responses
        expected_responses = [
            TokenPriceResponse(id=uuid.uuid4(), token_id=token_id, price_usd=price)
            for token_id, price in zip(token_ids, prices)
        ]

        usecase._TokenPriceUsecase__token_price_repo.create = AsyncMock(
            side_effect=expected_responses
        )

        # Execute concurrently
        import asyncio

        results = await asyncio.gather(
            *[usecase.create_token_price(tp) for tp in token_price_creates]
        )

        # Verify
        assert len(results) == 3
        for result, expected in zip(results, expected_responses):
            assert result == expected

        # Verify repository was called for each
        assert usecase._TokenPriceUsecase__token_price_repo.create.call_count == 3
