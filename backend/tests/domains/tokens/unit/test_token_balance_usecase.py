"""Unit tests for TokenBalanceUsecase."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.schemas.token_balance import (
    TokenBalanceCreate,
    TokenBalanceResponse,
)
from app.usecase.token_balance_usecase import TokenBalanceUsecase


class TestTokenBalanceUsecase:
    """Test TokenBalanceUsecase class."""

    def test_init(self, token_balance_usecase_with_di):
        """Test TokenBalanceUsecase initialization."""
        usecase = token_balance_usecase_with_di

        assert usecase._TokenBalanceUsecase__token_balance_repo is not None
        assert usecase._TokenBalanceUsecase__config_service is not None
        assert usecase._TokenBalanceUsecase__audit is not None

    @pytest.mark.asyncio
    async def test_create_token_balance_success(self, token_balance_usecase_with_di):
        """Test successful token balance creation."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 1000.5
        balance_usd = 1500.75

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenBalanceResponse(
            id=created_id,
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_balance(token_balance_create)

        # Verify
        assert result == expected_response
        assert result.id == created_id
        assert result.token_id == token_id
        assert result.wallet_id == wallet_id
        assert result.balance == balance
        assert result.balance_usd == balance_usd

        # Verify repository was called with correct data
        usecase._TokenBalanceUsecase__token_balance_repo.create.assert_called_once_with(
            token_balance_create
        )

        # Verify audit logging
        usecase._TokenBalanceUsecase__audit.info.assert_any_call(
            "token_balance_usecase_create_started",
            wallet_address=None,  # TokenBalanceCreate doesn't have wallet_address
        )
        usecase._TokenBalanceUsecase__audit.info.assert_any_call(
            "token_balance_usecase_create_success",
            token_balance_id=str(created_id),
        )

    @pytest.mark.asyncio
    async def test_create_token_balance_with_wallet_address(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation with wallet_address attribute."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 250.25
        balance_usd = 375.50

        # Create mock input with wallet_address attribute
        token_balance_create = Mock()
        token_balance_create.token_id = token_id
        token_balance_create.wallet_id = wallet_id
        token_balance_create.balance = balance
        token_balance_create.balance_usd = balance_usd
        token_balance_create.wallet_address = (
            "0x1234567890123456789012345678901234567890"
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenBalanceResponse(
            id=created_id,
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_balance(token_balance_create)

        # Verify
        assert result == expected_response

        # Verify audit logging includes wallet_address
        usecase._TokenBalanceUsecase__audit.info.assert_any_call(
            "token_balance_usecase_create_started",
            wallet_address="0x1234567890123456789012345678901234567890",
        )

    @pytest.mark.asyncio
    async def test_create_token_balance_zero_balance(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation with zero balance."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 0.0
        balance_usd = 0.0

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenBalanceResponse(
            id=created_id,
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_balance(token_balance_create)

        # Verify
        assert result == expected_response
        assert result.balance == 0.0
        assert result.balance_usd == 0.0

        # Verify audit logging
        usecase._TokenBalanceUsecase__audit.info.assert_any_call(
            "token_balance_usecase_create_success",
            token_balance_id=str(created_id),
        )

    @pytest.mark.asyncio
    async def test_create_token_balance_very_small_balance(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation with very small balance."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 0.000000001  # Very small balance
        balance_usd = 0.000001

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenBalanceResponse(
            id=created_id,
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_balance(token_balance_create)

        # Verify
        assert result == expected_response
        assert result.balance == balance
        assert result.balance_usd == balance_usd

    @pytest.mark.asyncio
    async def test_create_token_balance_very_large_balance(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation with very large balance."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 999999999999.99  # Very large balance
        balance_usd = 1500000000000.00

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenBalanceResponse(
            id=created_id,
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_balance(token_balance_create)

        # Verify
        assert result == expected_response
        assert result.balance == balance
        assert result.balance_usd == balance_usd

    @pytest.mark.asyncio
    async def test_create_token_balance_negative_balance(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation with negative balance."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = -100.0  # Negative balance (debt)
        balance_usd = -150.0

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository response
        created_id = uuid.uuid4()
        expected_response = TokenBalanceResponse(
            id=created_id,
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_balance(token_balance_create)

        # Verify
        assert result == expected_response
        assert result.balance == balance
        assert result.balance_usd == balance_usd

    @pytest.mark.asyncio
    async def test_create_token_balance_repository_exception(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation with repository exception."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 500.0
        balance_usd = 750.0

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository exception
        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database connection failed"):
            await usecase.create_token_balance(token_balance_create)

        # Verify audit logging
        usecase._TokenBalanceUsecase__audit.info.assert_any_call(
            "token_balance_usecase_create_started",
            wallet_address=None,
        )
        usecase._TokenBalanceUsecase__audit.error.assert_called_once_with(
            "token_balance_usecase_create_failed",
            error="Database connection failed",
        )

    @pytest.mark.asyncio
    async def test_create_token_balance_validation_error(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation with validation error."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 100.0
        balance_usd = 150.0

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository validation error
        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            side_effect=ValueError("Invalid token ID")
        )

        # Execute and verify exception
        with pytest.raises(ValueError, match="Invalid token ID"):
            await usecase.create_token_balance(token_balance_create)

        # Verify audit logging
        usecase._TokenBalanceUsecase__audit.error.assert_called_once_with(
            "token_balance_usecase_create_failed",
            error="Invalid token ID",
        )

    @pytest.mark.asyncio
    async def test_create_token_balance_result_without_id(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation when result doesn't have id attribute."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 75.0
        balance_usd = 112.5

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository response without id attribute
        mock_response = Mock(spec=["token_id", "wallet_id", "balance", "balance_usd"])
        mock_response.token_id = token_id
        mock_response.wallet_id = wallet_id
        mock_response.balance = balance
        mock_response.balance_usd = balance_usd

        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            return_value=mock_response
        )

        # Execute
        result = await usecase.create_token_balance(token_balance_create)

        # Verify
        assert result == mock_response
        assert result.token_id == token_id
        assert result.wallet_id == wallet_id
        assert result.balance == balance
        assert result.balance_usd == balance_usd

        # Verify audit logging with None for id
        usecase._TokenBalanceUsecase__audit.info.assert_any_call(
            "token_balance_usecase_create_success",
            token_balance_id=None,
        )

    @pytest.mark.asyncio
    async def test_create_token_balance_multiple_calls(
        self, token_balance_usecase_with_di
    ):
        """Test multiple token balance creations."""
        usecase = token_balance_usecase_with_di

        # First call
        token_id_1 = uuid.uuid4()
        wallet_id_1 = uuid.uuid4()
        balance_1 = 100.0
        balance_usd_1 = 150.0
        token_balance_create_1 = TokenBalanceCreate(
            token_id=token_id_1,
            wallet_id=wallet_id_1,
            balance=balance_1,
            balance_usd=balance_usd_1,
        )
        expected_response_1 = TokenBalanceResponse(
            id=uuid.uuid4(),
            token_id=token_id_1,
            wallet_id=wallet_id_1,
            balance=balance_1,
            balance_usd=balance_usd_1,
        )

        # Second call
        token_id_2 = uuid.uuid4()
        wallet_id_2 = uuid.uuid4()
        balance_2 = 200.0
        balance_usd_2 = 300.0
        token_balance_create_2 = TokenBalanceCreate(
            token_id=token_id_2,
            wallet_id=wallet_id_2,
            balance=balance_2,
            balance_usd=balance_usd_2,
        )
        expected_response_2 = TokenBalanceResponse(
            id=uuid.uuid4(),
            token_id=token_id_2,
            wallet_id=wallet_id_2,
            balance=balance_2,
            balance_usd=balance_usd_2,
        )

        # Mock repository responses
        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            side_effect=[expected_response_1, expected_response_2]
        )

        # Execute
        result_1 = await usecase.create_token_balance(token_balance_create_1)
        result_2 = await usecase.create_token_balance(token_balance_create_2)

        # Verify
        assert result_1 == expected_response_1
        assert result_2 == expected_response_2

        # Verify repository was called twice
        assert usecase._TokenBalanceUsecase__token_balance_repo.create.call_count == 2

        # Verify audit logging was called for both
        assert (
            usecase._TokenBalanceUsecase__audit.info.call_count == 4
        )  # 2 started + 2 success

    @pytest.mark.asyncio
    async def test_create_token_balance_concurrent_calls(
        self, token_balance_usecase_with_di
    ):
        """Test concurrent token balance creations."""
        usecase = token_balance_usecase_with_di

        # Create multiple inputs
        token_ids = [uuid.uuid4() for _ in range(3)]
        wallet_ids = [uuid.uuid4() for _ in range(3)]
        balances = [100.0, 200.0, 300.0]
        balance_usds = [150.0, 300.0, 450.0]

        token_balance_creates = [
            TokenBalanceCreate(
                token_id=token_id,
                wallet_id=wallet_id,
                balance=balance,
                balance_usd=balance_usd,
            )
            for token_id, wallet_id, balance, balance_usd in zip(
                token_ids, wallet_ids, balances, balance_usds
            )
        ]

        # Mock repository responses
        expected_responses = [
            TokenBalanceResponse(
                id=uuid.uuid4(),
                token_id=token_id,
                wallet_id=wallet_id,
                balance=balance,
                balance_usd=balance_usd,
            )
            for token_id, wallet_id, balance, balance_usd in zip(
                token_ids, wallet_ids, balances, balance_usds
            )
        ]

        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            side_effect=expected_responses
        )

        # Execute concurrently
        import asyncio

        results = await asyncio.gather(
            *[usecase.create_token_balance(tb) for tb in token_balance_creates]
        )

        # Verify
        assert len(results) == 3
        for result, expected in zip(results, expected_responses):
            assert result == expected

        # Verify repository was called for each
        assert usecase._TokenBalanceUsecase__token_balance_repo.create.call_count == 3

    @pytest.mark.asyncio
    async def test_create_token_balance_duplicate_entry(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation with duplicate entry."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 100.0
        balance_usd = 150.0

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository duplicate error
        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            side_effect=Exception("Token balance already exists for this wallet")
        )

        # Execute and verify exception
        with pytest.raises(
            Exception, match="Token balance already exists for this wallet"
        ):
            await usecase.create_token_balance(token_balance_create)

        # Verify audit logging
        usecase._TokenBalanceUsecase__audit.error.assert_called_once_with(
            "token_balance_usecase_create_failed",
            error="Token balance already exists for this wallet",
        )

    @pytest.mark.asyncio
    async def test_create_token_balance_mismatched_usd_value(
        self, token_balance_usecase_with_di
    ):
        """Test token balance creation with mismatched USD value."""
        usecase = token_balance_usecase_with_di
        token_id = uuid.uuid4()
        wallet_id = uuid.uuid4()
        balance = 100.0
        balance_usd = 0.0  # Mismatched - should be > 0 if balance > 0

        # Create input
        token_balance_create = TokenBalanceCreate(
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        # Mock repository response (repository doesn't validate this)
        created_id = uuid.uuid4()
        expected_response = TokenBalanceResponse(
            id=created_id,
            token_id=token_id,
            wallet_id=wallet_id,
            balance=balance,
            balance_usd=balance_usd,
        )

        usecase._TokenBalanceUsecase__token_balance_repo.create = AsyncMock(
            return_value=expected_response
        )

        # Execute
        result = await usecase.create_token_balance(token_balance_create)

        # Verify - should succeed as business logic validation is not in usecase
        assert result == expected_response
        assert result.balance == balance
        assert result.balance_usd == balance_usd
