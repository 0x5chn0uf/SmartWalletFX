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

    # Mock the EmailVerificationUsecase
    usecase_mock = AsyncMock()
    monkeypatch.setattr(ep, "EmailVerificationUsecase", lambda _: usecase_mock)

    resp = await ep.resend_verification_email(
        EmailVerificationRequest(email="nobody@example.com"),
        BackgroundTasks(),
        db=AsyncMock(),
    )

    # Verify the usecase was called with correct parameters
    usecase_mock.resend_verification.assert_awaited_once()
    assert isinstance(resp, ep.Response)


@pytest.mark.asyncio
async def test_resend_verification_email_failure(monkeypatch):
    # Mock the EmailVerificationUsecase to raise an exception
    usecase_mock = AsyncMock()
    usecase_mock.resend_verification.side_effect = HTTPException(
        status_code=500, detail="Internal error"
    )
    monkeypatch.setattr(ep, "EmailVerificationUsecase", lambda _: usecase_mock)

    with pytest.raises(HTTPException) as exc:
        await ep.resend_verification_email(
            EmailVerificationRequest(email="e@example.com"),
            BackgroundTasks(),
            db=AsyncMock(),
        )
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_resend_verification_success(monkeypatch):
    # Mock the EmailVerificationUsecase
    usecase_mock = AsyncMock()
    monkeypatch.setattr(ep, "EmailVerificationUsecase", lambda _: usecase_mock)

    tasks = BackgroundTasks()
    resp = await ep.resend_verification_email(
        EmailVerificationRequest(email="ok@example.com"), tasks, db=AsyncMock()
    )

    # Verify the usecase was called with correct parameters
    usecase_mock.resend_verification.assert_awaited_once_with(
        "ok@example.com", tasks, ep.verify_rate_limiter
    )
    assert isinstance(resp, ep.Response)


@pytest.mark.asyncio
async def test_verify_email_invalid_token(monkeypatch):
    # Mock the EmailVerificationUsecase to raise an exception
    usecase_mock = AsyncMock()
    usecase_mock.verify_email.side_effect = HTTPException(
        status_code=400, detail="Invalid or expired token"
    )
    monkeypatch.setattr(ep, "EmailVerificationUsecase", lambda _: usecase_mock)

    with pytest.raises(HTTPException):
        await ep.verify_email(
            EmailVerificationVerify(token="tok1234567"), db=AsyncMock()
        )

    usecase_mock.verify_email.assert_awaited_once_with("tok1234567")


@pytest.mark.asyncio
async def test_verify_email_user_not_found(monkeypatch):
    # Mock the EmailVerificationUsecase to raise an exception
    usecase_mock = AsyncMock()
    usecase_mock.verify_email.side_effect = HTTPException(
        status_code=400, detail="User not found"
    )
    monkeypatch.setattr(ep, "EmailVerificationUsecase", lambda _: usecase_mock)

    with pytest.raises(HTTPException):
        await ep.verify_email(
            EmailVerificationVerify(token="tok1234567"), db=AsyncMock()
        )

    usecase_mock.verify_email.assert_awaited_once_with("tok1234567")


@pytest.mark.asyncio
async def test_verify_email_success(monkeypatch):
    # Mock the EmailVerificationUsecase to return a successful response
    usecase_mock = AsyncMock()
    expected_response = {
        "access_token": "token",
        "refresh_token": "refresh",
        "token_type": "bearer",
        "expires_in": 3600,
    }
    usecase_mock.verify_email.return_value = expected_response
    monkeypatch.setattr(ep, "EmailVerificationUsecase", lambda _: usecase_mock)

    result = await ep.verify_email(
        EmailVerificationVerify(token="tok1234567"), db=AsyncMock()
    )

    usecase_mock.verify_email.assert_awaited_once_with("tok1234567")
    assert result == expected_response
