"""
Tests for email verification endpoints using dependency injection pattern.

This module tests the EmailVerification endpoint class that uses the singleton
pattern with dependency injection.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi import BackgroundTasks, HTTPException, Response

from app.domain.schemas.auth_token import TokenResponse
from app.domain.schemas.email_verification import (
    EmailVerificationRequest,
    EmailVerificationVerify,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_email_success(
    email_verification_endpoint_with_di, mock_email_verification_usecase
):
    """Test successful email verification."""
    endpoint = email_verification_endpoint_with_di

    # Mock the usecase response
    expected_response = TokenResponse(
        access_token="access_token_value",
        refresh_token="refresh_token_value",
        token_type="bearer",
        expires_in=3600,
    )
    mock_email_verification_usecase.verify_email.return_value = expected_response

    # Test the endpoint method
    payload = EmailVerificationVerify(token="test_token")
    mock_response = Mock(spec=Response)
    result = await endpoint.verify_email(payload, mock_response)

    # Verify the usecase was called correctly
    mock_email_verification_usecase.verify_email.assert_awaited_once_with("test_token")
    assert result == expected_response

    # Verify cookies are set
    assert mock_response.set_cookie.call_count == 2
    # Check access token cookie
    access_cookie_call = mock_response.set_cookie.call_args_list[0]
    assert access_cookie_call[0][0] == "access_token"
    assert access_cookie_call[0][1] == "access_token_value"
    assert access_cookie_call[1]["httponly"] is True
    assert access_cookie_call[1]["samesite"] == "lax"
    # Check refresh token cookie
    refresh_cookie_call = mock_response.set_cookie.call_args_list[1]
    assert refresh_cookie_call[0][0] == "refresh_token"
    assert refresh_cookie_call[0][1] == "refresh_token_value"
    assert refresh_cookie_call[1]["httponly"] is True
    assert refresh_cookie_call[1]["samesite"] == "lax"
    assert refresh_cookie_call[1]["path"] == "/auth"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_email_invalid_token(
    email_verification_endpoint_with_di, mock_email_verification_usecase
):
    """Test email verification with invalid token."""
    endpoint = email_verification_endpoint_with_di

    # Mock the usecase to raise an exception
    mock_email_verification_usecase.verify_email.side_effect = HTTPException(
        status_code=400, detail="Invalid or expired token"
    )

    # Test the endpoint method
    payload = EmailVerificationVerify(token="invalid_token")
    mock_response = Mock(spec=Response)
    with pytest.raises(HTTPException) as exc_info:
        await endpoint.verify_email(payload, mock_response)

    # Verify the exception details
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired token"
    mock_email_verification_usecase.verify_email.assert_awaited_once_with(
        "invalid_token"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_email_user_not_found(
    email_verification_endpoint_with_di, mock_email_verification_usecase
):
    """Test email verification when user is not found."""
    endpoint = email_verification_endpoint_with_di

    # Mock the usecase to raise an exception
    mock_email_verification_usecase.verify_email.side_effect = HTTPException(
        status_code=400, detail="User not found"
    )

    # Test the endpoint method
    payload = EmailVerificationVerify(token="test_token")
    mock_response = Mock(spec=Response)
    with pytest.raises(HTTPException) as exc_info:
        await endpoint.verify_email(payload, mock_response)

    # Verify the exception details
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User not found"
    mock_email_verification_usecase.verify_email.assert_awaited_once_with("test_token")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resend_verification_email_success(
    email_verification_endpoint_with_di,
    mock_email_verification_usecase,
    mock_email_service,
):
    """Test successful resend verification email using mocks."""
    endpoint = email_verification_endpoint_with_di

    # Mock the usecase
    mock_email_verification_usecase.resend_verification.return_value = None

    # Test the endpoint method
    payload = EmailVerificationRequest(email="test@example.com")
    background_tasks = BackgroundTasks()

    result = await endpoint.resend_verification_email(payload, background_tasks)

    # Verify the usecase was called correctly
    mock_email_verification_usecase.resend_verification.assert_awaited_once()
    # Verify the response
    assert result.status_code == 204


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resend_verification_email_failure(
    email_verification_endpoint_with_di, mock_email_verification_usecase
):
    """Test resend verification email with failure."""
    endpoint = email_verification_endpoint_with_di

    # Mock the usecase to raise an exception
    mock_email_verification_usecase.resend_verification.side_effect = HTTPException(
        status_code=500, detail="Internal error"
    )

    # Test the endpoint method
    payload = EmailVerificationRequest(email="test@example.com")
    background_tasks = BackgroundTasks()

    with pytest.raises(HTTPException) as exc_info:
        await endpoint.resend_verification_email(payload, background_tasks)

    # Verify the exception details
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Internal error"
    mock_email_verification_usecase.resend_verification.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resend_verification_email_unknown_user(
    email_verification_endpoint_with_di,
    mock_email_verification_usecase,
):
    """Test resend verification email for unknown user."""
    endpoint = email_verification_endpoint_with_di

    # Mock the usecase to complete successfully (even for unknown users)
    mock_email_verification_usecase.resend_verification.return_value = None

    # Test the endpoint method
    payload = EmailVerificationRequest(email="unknown@example.com")
    background_tasks = BackgroundTasks()

    result = await endpoint.resend_verification_email(payload, background_tasks)

    # Verify the usecase was called correctly
    mock_email_verification_usecase.resend_verification.assert_awaited_once()
    # Verify the response (should return 204 even for unknown users for security)
    assert result.status_code == 204


@pytest.mark.unit
@pytest.mark.asyncio
async def test_endpoint_has_correct_router_configuration(
    email_verification_endpoint_with_di,
):
    """Test that the endpoint has correct router configuration."""
    endpoint = email_verification_endpoint_with_di

    # Verify router configuration
    assert endpoint.ep.prefix == "/auth"
    assert "auth" in endpoint.ep.tags

    # Verify routes are properly configured
    route_paths = [route.path for route in endpoint.ep.routes]
    assert "/auth/verify-email" in route_paths
    assert "/auth/resend-verification" in route_paths


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resend_verification_email_service_failure(
    email_verification_endpoint_with_di,
    mock_email_service,
    mock_email_verification_usecase,
):
    """Test resend verification email when email service experiences failures."""

    async def resend_side_effect(email, background_tasks, _rate_limiter):
        background_tasks.add_task(
            mock_email_service.send_verification_email,
            email,
            "tok123",
        )

    mock_email_verification_usecase.resend_verification.side_effect = resend_side_effect

    endpoint = email_verification_endpoint_with_di

    payload = EmailVerificationRequest(email="fail@example.com")
    background_tasks = BackgroundTasks()
    result = await endpoint.resend_verification_email(payload, background_tasks)
    await background_tasks()

    assert result.status_code == 204
    mock_email_service.send_verification_email.assert_awaited_once_with(
        "fail@example.com",
        "tok123",
    )
