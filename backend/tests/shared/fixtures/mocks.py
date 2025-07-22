"""External service mocking fixtures for the test suite."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mocks the ARBITRUM_RPC_URL setting.

    This is a temporary measure to ensure test isolation until a more
    performant solution (like transactional fixtures) is implemented.
    """
    monkeypatch.setattr(
        "app.core.config.Configuration.ARBITRUM_RPC_URL",
        "http://mock-rpc",
        raising=False,
    )
    yield


@pytest.fixture
def mock_async_session():
    """Create a mock AsyncSession for testing."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_redis():
    """
    Mock Redis client for testing.
    Provides a mock Redis client that can be used to test Redis-dependent code.
    """
    mock_client = Mock()
    mock_client.get = Mock(return_value=None)
    mock_client.set = Mock(return_value=True)
    mock_client.delete = Mock(return_value=1)
    mock_client.exists = Mock(return_value=0)
    mock_client.expire = Mock(return_value=True)
    mock_client.close = Mock()

    with patch("app.core.redis.redis_client", mock_client):
        yield mock_client


@pytest.fixture
def mock_web3():
    """
    Mock Web3 client for blockchain testing.
    Provides a mock Web3 client for testing blockchain interactions.
    """
    mock_web3 = Mock()
    mock_web3.eth = Mock()
    mock_web3.eth.contract = Mock()
    mock_web3.eth.get_balance = Mock(return_value=1000000000000000000)  # 1 ETH
    mock_web3.eth.get_block_number = Mock(return_value=12345)

    # Mock contract calls
    mock_contract = Mock()
    mock_contract.functions = Mock()
    mock_contract.functions.balanceOf = Mock()
    mock_contract.functions.balanceOf.return_value.call = Mock(return_value=1000000)
    mock_web3.eth.contract.return_value = mock_contract

    with patch("app.core.dependencies.get_w3", return_value=mock_web3):
        yield mock_web3


@pytest.fixture
def mock_httpx_client():
    """
    Mock HTTPX client for external API testing.
    Provides a mock HTTPX client for testing external API calls.
    """
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={"success": True})
    mock_response.text = "success"
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.put = AsyncMock(return_value=mock_response)
    mock_client.delete = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_celery():
    """
    Mock Celery for background task testing.
    Provides a mock Celery instance for testing background tasks.
    """
    mock_celery = Mock()
    mock_task = Mock()
    mock_task.delay = Mock(return_value=Mock())
    mock_task.apply_async = Mock(return_value=Mock())
    mock_celery.send_task = Mock(return_value=mock_task)

    with patch("app.celery_app.celery", mock_celery):
        yield mock_celery


@pytest.fixture
def mock_password_hasher():
    """
    Mock password hasher for authentication testing.
    Provides a mock password hasher for testing password operations.
    """
    mock_hasher = Mock()
    mock_hasher.hash_password = Mock(return_value="hashed_password")
    mock_hasher.verify_password = Mock(return_value=True)

    with patch("app.utils.security.PasswordHasher", mock_hasher):
        yield mock_hasher


@pytest.fixture
def mock_rate_limiter_utils():
    """
    Mock rate limiter utils for testing.
    Provides a mock rate limiter for testing rate limiting functionality.
    """
    mock_rate_limiter = Mock()
    mock_rate_limiter.login_rate_limiter = Mock()
    mock_rate_limiter.login_rate_limiter.allow = Mock(return_value=True)

    return mock_rate_limiter


@pytest.fixture
def mock_all_external_services(
    mock_redis,
    mock_web3,
    mock_httpx_client,
    mock_celery,
    mock_password_hasher,
):
    """
    Comprehensive mock for all external services.
    This fixture combines all external service mocks for complete test isolation.
    """
    yield {
        "redis": mock_redis,
        "web3": mock_web3,
        "httpx": mock_httpx_client,
        "celery": mock_celery,
        "password_hasher": mock_password_hasher,
    }
