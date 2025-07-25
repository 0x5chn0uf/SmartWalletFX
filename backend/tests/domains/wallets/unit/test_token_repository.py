import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest

from app.domain.schemas.token import TokenCreate
from app.models.token import Token
from app.repositories.token_repository import TokenRepository


def setup_mock_session(repository, mock_session):
    """Helper function to set up mock session for repository tests."""

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    # Patch the repository's database service get_session method
    repository._TokenRepository__database.get_session = mock_get_session


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_repository_create(token_repository_with_di, mock_async_session):
    """Test token creation with dependency injection."""
    # Setup mock session
    setup_mock_session(token_repository_with_di, mock_async_session)

    # Create test data
    address = f"0x{uuid.uuid4().hex[:40]}"
    token_data = TokenCreate(
        address=address,
        symbol="TKN",
        name="MockToken",
        decimals=18,
    )

    # Mock the token creation process
    created_token = Token(
        id=uuid.uuid4(),
        address=address,
        symbol="TKN",
        name="MockToken",
        decimals=18,
    )

    # Mock the session methods properly
    async def mock_refresh(obj):
        obj.id = created_token.id
        return obj

    mock_async_session.refresh = mock_refresh

    # Execute the test
    await token_repository_with_di.create(token_data)

    # Verify the results
    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_repository_create_exception(
    token_repository_with_di, mock_async_session
):
    """Test token creation with database exception handling."""
    # Setup mock session
    setup_mock_session(token_repository_with_di, mock_async_session)

    # Create test data
    address = f"0x{uuid.uuid4().hex[:40]}"
    token_data = TokenCreate(
        address=address,
        symbol="TKN",
        name="MockToken",
        decimals=18,
    )

    # Configure mock to raise exception during commit
    mock_async_session.add = Mock()
    mock_async_session.commit = AsyncMock(side_effect=Exception("Database error"))

    # Execute and verify exception is raised
    with pytest.raises(Exception, match="Database error"):
        await token_repository_with_di.create(token_data)

    # Verify the operations that should have been called
    mock_async_session.add.assert_called_once()
    mock_async_session.commit.assert_awaited_once()
