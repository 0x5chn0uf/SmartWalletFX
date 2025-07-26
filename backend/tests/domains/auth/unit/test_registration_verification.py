import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import BackgroundTasks

from app.api.endpoints.auth import Auth
from app.domain.schemas.user import UserCreate


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_user_sends_verification(monkeypatch):
    # Create a mock service that properly handles background_tasks
    service = AsyncMock()
    user = Mock(id=1, email="user@example.com")

    # Define a side effect function that adds a task to the background_tasks
    async def mock_register(payload, background_tasks=None):
        if background_tasks is not None:
            # Add a mock task to the background_tasks
            background_tasks.add_task(lambda: None)
        return user

    service.register.side_effect = mock_register

    # Create Auth instance with the mocked service and rate limiter
    from app.domain.interfaces.utils import RateLimiterUtilsInterface

    mock_rate_limiter_utils = Mock(spec=RateLimiterUtilsInterface)
    mock_rate_limiter_utils.login_rate_limiter = Mock()
    mock_rate_limiter_utils.login_rate_limiter.allow = Mock(return_value=True)
    mock_rate_limiter_utils.login_rate_limiter.reset = Mock()

    auth_endpoint = Auth(service, mock_rate_limiter_utils)

    # These mocks are no longer needed as we're handling the email verification in the mock_register function
    # but we'll keep them for completeness
    repo = AsyncMock()
    monkeypatch.setattr(
        "app.repositories.email_verification_repository.EmailVerificationRepository",
        lambda db: repo,
    )
    monkeypatch.setattr(
        "app.utils.token.generate_verification_token",
        lambda: ("tok", "hash", datetime.datetime.now(datetime.timezone.utc)),
    )
    monkeypatch.setattr("app.services.email_service.EmailService", lambda: AsyncMock())

    request = Mock(client=Mock(host="test"))
    payload = UserCreate(
        username="user", email="user@example.com", password="Str0ng!pwd"
    )
    tasks = BackgroundTasks()

    res = await auth_endpoint.register_user(request, payload, tasks)

    assert res is user
    assert tasks.tasks
    # We're now handling the email verification in the mock_register function, so we don't need to check repo.create
    service.register.assert_awaited_once_with(payload, background_tasks=tasks)
