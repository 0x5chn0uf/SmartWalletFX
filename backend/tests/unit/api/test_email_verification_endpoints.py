from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.api.endpoints import email_verification as ep
from app.schemas.email_verification import (
    EmailVerificationRequest,
    EmailVerificationVerify,
)


@pytest.mark.asyncio
async def test_resend_verification_rate_limited(monkeypatch):
    monkeypatch.setattr(ep.verify_rate_limiter, "allow", lambda _: False)
    payload = EmailVerificationRequest(email="foo@example.com")
    with pytest.raises(HTTPException) as exc:
        await ep.resend_verification_email(payload, BackgroundTasks(), db=AsyncMock())
    assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_resend_verification_unknown_user(monkeypatch):
    monkeypatch.setattr(ep.verify_rate_limiter, "allow", lambda _: True)
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = None
    monkeypatch.setattr(ep, "UserRepository", lambda _: user_repo)
    resp = await ep.resend_verification_email(
        EmailVerificationRequest(email="nobody@example.com"),
        BackgroundTasks(),
        db=AsyncMock(),
    )
    assert isinstance(resp, ep.Response)


@pytest.mark.asyncio
async def test_resend_verification_email_failure(monkeypatch):
    monkeypatch.setattr(ep.verify_rate_limiter, "allow", lambda _: True)
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = Mock(
        id=1, email="e@example.com", email_verified=False
    )
    monkeypatch.setattr(ep, "UserRepository", lambda _: user_repo)
    repo = AsyncMock()
    monkeypatch.setattr(ep, "EmailVerificationRepository", lambda _: repo)
    monkeypatch.setattr(
        ep,
        "generate_verification_token",
        lambda: ("tok", "hash", datetime.now(timezone.utc)),
    )
    monkeypatch.setattr(ep, "EmailService", lambda: AsyncMock())
    tasks = BackgroundTasks()

    def boom(*args, **kwargs):
        raise Exception("boom")

    monkeypatch.setattr(tasks, "add_task", boom)

    with pytest.raises(HTTPException) as exc:
        await ep.resend_verification_email(
            EmailVerificationRequest(email="e@example.com"), tasks, db=AsyncMock()
        )
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_resend_verification_success(monkeypatch):
    monkeypatch.setattr(ep.verify_rate_limiter, "allow", lambda _: True)
    user = Mock(id=2, email="ok@example.com", email_verified=False)
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = user
    monkeypatch.setattr(ep, "UserRepository", lambda _: user_repo)
    repo = AsyncMock()
    monkeypatch.setattr(ep, "EmailVerificationRepository", lambda _: repo)
    monkeypatch.setattr(
        ep,
        "generate_verification_token",
        lambda: ("tok", "hash", datetime.now(timezone.utc)),
    )
    service = AsyncMock()
    monkeypatch.setattr(ep, "EmailService", lambda: service)

    tasks = BackgroundTasks()
    resp = await ep.resend_verification_email(
        EmailVerificationRequest(email=user.email), tasks, db=AsyncMock()
    )
    assert isinstance(resp, ep.Response)
    service.send_email_verification.assert_not_called()
    assert tasks.tasks


@pytest.mark.asyncio
async def test_verify_email_invalid_token(monkeypatch):
    repo = AsyncMock()
    repo.get_valid.return_value = None
    monkeypatch.setattr(ep, "EmailVerificationRepository", lambda _: repo)
    with pytest.raises(HTTPException):
        await ep.verify_email(
            EmailVerificationVerify(token="tok1234567"), db=AsyncMock()
        )


@pytest.mark.asyncio
async def test_verify_email_user_not_found(monkeypatch):
    ev = Mock(user_id=1)
    repo = AsyncMock()
    repo.get_valid.return_value = ev
    monkeypatch.setattr(ep, "EmailVerificationRepository", lambda _: repo)
    user_repo = AsyncMock()
    user_repo.get_by_id.return_value = None
    monkeypatch.setattr(ep, "UserRepository", lambda _: user_repo)
    with pytest.raises(HTTPException):
        await ep.verify_email(
            EmailVerificationVerify(token="tok1234567"), db=AsyncMock()
        )


@pytest.mark.asyncio
async def test_verify_email_success(monkeypatch):
    ev = Mock(user_id=2)
    repo = AsyncMock()
    repo.get_valid.return_value = ev
    monkeypatch.setattr(ep, "EmailVerificationRepository", lambda _: repo)
    user = Mock(id=2)
    user_repo = AsyncMock()
    user_repo.get_by_id.return_value = user
    monkeypatch.setattr(ep, "UserRepository", lambda _: user_repo)
    db = AsyncMock()
    res = await ep.verify_email(EmailVerificationVerify(token="tok1234567"), db=db)
    assert res == {"status": "verified"}
    db.commit.assert_awaited()
    repo.mark_used.assert_awaited_with(ev)
