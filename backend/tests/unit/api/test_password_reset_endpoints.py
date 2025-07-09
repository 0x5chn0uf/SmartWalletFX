from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.api.endpoints import password_reset as ep
from app.schemas.password_reset import (
    PasswordResetComplete,
    PasswordResetRequest,
    PasswordResetVerify,
)


@pytest.mark.asyncio
async def test_request_password_reset_rate_limited(monkeypatch):
    monkeypatch.setattr(ep.reset_rate_limiter, "allow", lambda _: False)
    payload = PasswordResetRequest(email="foo@example.com")
    with pytest.raises(HTTPException) as exc:
        await ep.request_password_reset(payload, BackgroundTasks(), db=AsyncMock())
    assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_request_password_reset_unknown_email(monkeypatch):
    monkeypatch.setattr(ep.reset_rate_limiter, "allow", lambda _: True)
    mock_repo = AsyncMock()
    mock_repo.get_by_email.return_value = None
    monkeypatch.setattr(ep, "UserRepository", lambda _: mock_repo)
    resp = await ep.request_password_reset(
        PasswordResetRequest(email="nobody@example.com"),
        BackgroundTasks(),
        db=AsyncMock(),
    )
    assert resp is None


@pytest.mark.asyncio
async def test_request_password_reset_email_failure(monkeypatch):
    monkeypatch.setattr(ep.reset_rate_limiter, "allow", lambda _: True)
    mock_repo = AsyncMock()
    mock_repo.get_by_email.return_value = Mock(id=1, email="e@example.com")
    monkeypatch.setattr(ep, "UserRepository", lambda _: mock_repo)
    pr_repo = AsyncMock()
    monkeypatch.setattr(ep, "PasswordResetRepository", lambda _: pr_repo)
    monkeypatch.setattr(
        ep, "generate_token", lambda: ("tok", "hash", datetime.now(timezone.utc))
    )

    monkeypatch.setattr(ep, "EmailService", lambda: AsyncMock())
    tasks = BackgroundTasks()

    def boom(*args, **kwargs):
        raise Exception("boom")

    monkeypatch.setattr(tasks, "add_task", boom)

    with pytest.raises(HTTPException) as exc:
        await ep.request_password_reset(
            PasswordResetRequest(email="e@example.com"), tasks, db=AsyncMock()
        )
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_request_password_reset_success(monkeypatch):
    monkeypatch.setattr(ep.reset_rate_limiter, "allow", lambda _: True)
    user = Mock(id=2, email="ok@example.com")
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = user
    monkeypatch.setattr(ep, "UserRepository", lambda _: user_repo)
    pr_repo = AsyncMock()
    monkeypatch.setattr(ep, "PasswordResetRepository", lambda _: pr_repo)
    monkeypatch.setattr(
        ep, "generate_token", lambda: ("tok", "hash", datetime.now(timezone.utc))
    )

    service = AsyncMock()
    monkeypatch.setattr(ep, "EmailService", lambda: service)

    tasks = BackgroundTasks()
    resp = await ep.request_password_reset(
        PasswordResetRequest(email=user.email), tasks, db=AsyncMock()
    )
    assert isinstance(resp, ep.Response)
    service.send_password_reset.assert_not_called()  # added as background task
    assert tasks.tasks


@pytest.mark.asyncio
async def test_verify_reset_token(monkeypatch):
    repo = AsyncMock()
    repo.get_valid.return_value = object()
    monkeypatch.setattr(ep, "PasswordResetRepository", lambda _: repo)
    res = await ep.verify_reset_token(
        PasswordResetVerify(token="tok1234567"), db=AsyncMock()
    )
    assert res == {"valid": True}


@pytest.mark.asyncio
async def test_verify_reset_token_invalid(monkeypatch):
    repo = AsyncMock()
    repo.get_valid.return_value = None
    monkeypatch.setattr(ep, "PasswordResetRepository", lambda _: repo)
    res = await ep.verify_reset_token(
        PasswordResetVerify(token="tok1234567"), db=AsyncMock()
    )
    assert res == {"valid": False}


@pytest.mark.asyncio
async def test_reset_password_invalid_token(monkeypatch):
    repo = AsyncMock()
    repo.get_valid.return_value = None
    monkeypatch.setattr(ep, "PasswordResetRepository", lambda _: repo)
    with pytest.raises(HTTPException):
        await ep.reset_password(
            PasswordResetComplete(token="badtoken12", password="Validpass1"),
            db=AsyncMock(),
        )


@pytest.mark.asyncio
async def test_reset_password_user_not_found(monkeypatch):
    pr = Mock(user_id=1)
    repo = AsyncMock()
    repo.get_valid.return_value = pr
    monkeypatch.setattr(ep, "PasswordResetRepository", lambda _: repo)
    user_repo = AsyncMock()
    user_repo.get_by_id.return_value = None
    monkeypatch.setattr(ep, "UserRepository", lambda _: user_repo)
    with pytest.raises(HTTPException):
        await ep.reset_password(
            PasswordResetComplete(token="tok1234567", password="Validpass1"),
            db=AsyncMock(),
        )


@pytest.mark.asyncio
async def test_reset_password_success(monkeypatch):
    pr = Mock(user_id=2)
    repo = AsyncMock()
    repo.get_valid.return_value = pr
    monkeypatch.setattr(ep, "PasswordResetRepository", lambda _: repo)
    user = Mock(id=2)
    user_repo = AsyncMock()
    user_repo.get_by_id.return_value = user
    monkeypatch.setattr(ep, "UserRepository", lambda _: user_repo)
    monkeypatch.setattr(
        "app.utils.security.PasswordHasher.hash_password", lambda pw: "hash"
    )
    db = AsyncMock()
    res = await ep.reset_password(
        PasswordResetComplete(token="tok1234567", password="Validpass1"), db=db
    )
    assert res == {"status": "success"}
    db.commit.assert_awaited()
    repo.mark_used.assert_awaited_with(pr)
