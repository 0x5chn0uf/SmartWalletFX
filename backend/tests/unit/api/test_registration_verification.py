import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import BackgroundTasks

from app.api.endpoints import auth as ep
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_register_user_sends_verification(monkeypatch):
    service = AsyncMock()
    user = Mock(id=1, email="user@example.com")
    service.register.return_value = user
    monkeypatch.setattr(ep, "AuthService", lambda db: service)

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

    res = await ep.register_user(request, payload, tasks, db=AsyncMock())

    assert res is user
    assert tasks.tasks
    repo.create.assert_awaited()
    assert user.verification_deadline is not None
