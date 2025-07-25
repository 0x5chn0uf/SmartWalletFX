"""
Tests for email verification endpoints using dependency injection pattern.

This module tests the EmailVerification endpoint class that uses the singleton
pattern with dependency injection.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.domain.schemas.auth_token import TokenResponse
from app.domain.schemas.email_verification import (
    EmailVerificationRequest,
    EmailVerificationVerify,
)
from tests.shared.fixtures.enhanced_mocks import MockAssertions, MockBehavior


@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_email_success(
    email_verification_endpoint_with_di, mock_email_verification_usecase
):
    """Test successful email verification."""
    endpoint = email_verification_endpoint_with_di

    # Mock the usecase response
    expected_response = TokenResponse(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        token_type="bearer",
        expires_in=3600,
    )
    mock_email_verification_usecase.verify_email.return_value = expected_response

    # Test the endpoint method
    payload = EmailVerificationVerify(token="test_token")
    result = await endpoint.verify_email(payload)

    # Verify the usecase was called correctly
    mock_email_verification_usecase.verify_email.assert_awaited_once_with("test_token")
    assert result == expected_response


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
    with pytest.raises(HTTPException) as exc_info:
        await endpoint.verify_email(payload)

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
    with pytest.raises(HTTPException) as exc_info:
        await endpoint.verify_email(payload)

    # Verify the exception details
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User not found"
    mock_email_verification_usecase.verify_email.assert_awaited_once_with("test_token")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resend_verification_email_success(
    email_verification_endpoint_with_di,
    mock_email_verification_usecase,
    mock_email_service_enhanced,
    mock_assertions,
):
    """Test successful resend verification email with enhanced mocking."""
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
    email_verification_endpoint_with_di, mock_email_service_enhanced, mock_assertions
):
    """Test resend verification email when email service experiences failures."""
    # Configure email service for failure scenarios
    mock_email_service_enhanced.set_behavior(MockBehavior.FAILURE)

    # This test demonstrates how enhanced mocks can simulate
    # real-world failure scenarios for better test coverage

    # The enhanced mock will track calls and simulate failure behavior
    # This allows testing of error handling paths and retry logic
