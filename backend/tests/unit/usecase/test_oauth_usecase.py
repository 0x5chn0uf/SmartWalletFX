from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from app.domain.schemas.auth_token import TokenResponse
from app.models.user import User
from app.usecase.oauth_usecase import OAuthUsecase


def create_mock_usecase():
    """Helper to create OAuthUsecase with mocked dependencies"""
    oauth_account_repo = Mock()
    user_repo = Mock()
    refresh_token_repo = Mock()
    oauth_service = Mock()
    config_service = Mock()
    audit = Mock()

    return OAuthUsecase(
        oauth_account_repo=oauth_account_repo,
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        oauth_service=oauth_service,
        config_service=config_service,
        audit=audit,
    )


@pytest.mark.asyncio
async def test_authenticate_and_issue_tokens():
    # Setup
    usecase = create_mock_usecase()

    # Mock the oauth_service methods
    mock_user = User(id=1, email="test@example.com", username="testuser")
    mock_tokens = TokenResponse(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=3600,  # Add required field
    )

    usecase._OAuthUsecase__oauth_service.authenticate_or_create = AsyncMock(
        return_value=mock_user
    )
    usecase._OAuthUsecase__oauth_service.issue_tokens = AsyncMock(
        return_value=mock_tokens
    )

    # Execute
    user, tokens = await usecase.authenticate_and_issue_tokens(
        "google", "sub123", "test@example.com"
    )

    # Assert
    assert user == mock_user
    assert tokens == mock_tokens
    usecase._OAuthUsecase__oauth_service.authenticate_or_create.assert_called_once_with(
        "google", "sub123", "test@example.com"
    )
    usecase._OAuthUsecase__oauth_service.issue_tokens.assert_called_once_with(
        mock_user
    )


@pytest.mark.asyncio
async def test_generate_login_redirect_success():
    # Setup
    usecase = create_mock_usecase()

    # Mock the _build_auth_url method
    usecase._build_auth_url = Mock(return_value="https://auth.example.com")

    # Mock redis with async behavior
    mock_redis = AsyncMock()

    # Execute
    result = await usecase.generate_login_redirect("google", mock_redis)

    # Assert
    assert isinstance(result, RedirectResponse)
    assert result.status_code == 307


@pytest.mark.asyncio
async def test_generate_login_redirect_unsupported_provider():
    # Setup
    usecase = create_mock_usecase()
    mock_redis = AsyncMock()

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await usecase.generate_login_redirect("unsupported", mock_redis)
    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test_process_callback_success():
    # Setup
    usecase = create_mock_usecase()
    
    # Mock config service
    usecase._OAuthUsecase__config_service.FRONTEND_BASE_URL = "https://example.com"
    usecase._OAuthUsecase__config_service.OAUTH_REDIRECT_URI = "https://example.com/oauth/{provider}/callback"

    # Mock request
    mock_request = Mock(spec=Request)
    mock_request.cookies = {"oauth_state": "state123"}
    
    # Mock redis
    mock_redis = AsyncMock()

    # Mock dependencies
    usecase._exchange_code = AsyncMock(
        return_value={"sub": "123", "email": "test@example.com"}
    )
    mock_user = Mock()
    mock_user.id = 1
    mock_tokens = Mock()
    usecase.authenticate_and_issue_tokens = AsyncMock(return_value=(mock_user, mock_tokens))

    # Mock verify_state function
    with patch("app.usecase.oauth_usecase.verify_state", return_value=True):
        # Execute
        result = await usecase.process_callback(mock_request, "google", "code123", "state123", mock_redis)

        # Assert
        assert result is not None


@pytest.mark.asyncio
async def test_process_callback_unsupported_provider():
    # Setup
    usecase = create_mock_usecase()
    
    # Mock request
    mock_request = Mock(spec=Request)
    mock_request.cookies = {"oauth_state": "state123"}
    
    # Mock redis
    mock_redis = AsyncMock()

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await usecase.process_callback(mock_request, "unsupported", "code123", "state123", mock_redis)
    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test_process_callback_state_mismatch():
    # Setup
    usecase = create_mock_usecase()
    
    # Mock request with different state than what's passed to the callback
    mock_request = Mock(spec=Request)
    mock_request.cookies = {"oauth_state": "cookie_state123"}
    
    # Mock redis
    mock_redis = AsyncMock()

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await usecase.process_callback(mock_request, "google", "code123", "different_state456", mock_redis)
    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_process_callback_invalid_state():
    # Setup
    usecase = create_mock_usecase()
    
    # Mock request
    mock_request = Mock(spec=Request)
    mock_request.cookies = {"oauth_state": "invalid_state"}
    
    # Mock redis
    mock_redis = AsyncMock()

    # Execute and Assert
    with patch("app.usecase.oauth_usecase.verify_state", return_value=False):
        with pytest.raises(HTTPException) as excinfo:
            await usecase.process_callback(mock_request, "google", "code123", "invalid_state", mock_redis)
        assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_process_callback_missing_sub():
    # Setup
    usecase = create_mock_usecase()
    usecase._OAuthUsecase__config_service.OAUTH_REDIRECT_URI = "https://example.com/oauth/{provider}/callback"
    usecase._exchange_code = AsyncMock(
        return_value={"email": "test@example.com"}
    )  # Missing sub
    
    # Mock request
    mock_request = Mock(spec=Request)
    mock_request.cookies = {"oauth_state": "state123"}
    
    # Mock redis
    mock_redis = AsyncMock()

    # Execute and Assert
    with patch("app.usecase.oauth_usecase.verify_state", return_value=True):
        with pytest.raises(HTTPException) as excinfo:
            await usecase.process_callback(mock_request, "google", "code123", "state123", mock_redis)
        assert excinfo.value.status_code == 400


def test_build_auth_url_google():
    # Setup
    usecase = create_mock_usecase()
    usecase._OAuthUsecase__config_service.GOOGLE_CLIENT_ID = "google_client_id"
    usecase._OAuthUsecase__config_service.GOOGLE_REDIRECT_URI = (
        "https://example.com/callback"
    )

    # Execute
    result = usecase._build_auth_url("google", "test_state")

    # Assert
    assert "accounts.google.com" in result
    assert "google_client_id" in result
    assert "test_state" in result


def test_build_auth_url_github():
    # Setup
    usecase = create_mock_usecase()
    usecase._OAuthUsecase__config_service.GITHUB_CLIENT_ID = "github_client_id"
    usecase._OAuthUsecase__config_service.GITHUB_REDIRECT_URI = (
        "https://example.com/callback"
    )

    # Execute
    result = usecase._build_auth_url("github", "test_state")

    # Assert
    assert "github.com" in result
    assert "github_client_id" in result
    assert "test_state" in result


def test_build_auth_url_unsupported():
    # Setup
    usecase = create_mock_usecase()

    # Execute and Assert
    with pytest.raises(ValueError) as excinfo:
        usecase._build_auth_url("unsupported", "test_state")
    assert "Unsupported provider" in str(excinfo.value)


@pytest.mark.asyncio
async def test_exchange_code_google():
    # Setup
    usecase = create_mock_usecase()
    usecase._OAuthUsecase__config_service.GOOGLE_CLIENT_ID = "google_client_id"
    usecase._OAuthUsecase__config_service.GOOGLE_CLIENT_SECRET = "google_secret"
    usecase._OAuthUsecase__config_service.GOOGLE_REDIRECT_URI = (
        "https://example.com/callback"
    )

    # Mock httpx response
    mock_response = Mock()
    mock_response.json.return_value = {"id_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20ifQ.fake_signature"}
    mock_response.raise_for_status = Mock()

    # Mock jwt decode
    with pytest.mock.patch(
        "httpx.AsyncClient.post", return_value=mock_response
    ), pytest.mock.patch(
        "jose.jwt.decode", return_value={"sub": "123", "email": "test@example.com"}
    ):
        # Execute
        result = await usecase._exchange_code("google", "auth_code", "https://example.com/callback")

        # Assert
        assert result["sub"] == "123"
        assert result["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_exchange_code_google_missing_id_token():
    # Setup
    usecase = create_mock_usecase()
    usecase._OAuthUsecase__config_service.GOOGLE_CLIENT_ID = "google_client_id"
    usecase._OAuthUsecase__config_service.GOOGLE_CLIENT_SECRET = "google_secret"
    usecase._OAuthUsecase__config_service.GOOGLE_REDIRECT_URI = (
        "https://example.com/callback"
    )

    # Mock httpx response without id_token
    mock_response = Mock()
    mock_response.json.return_value = {"access_token": "token"}
    mock_response.raise_for_status = Mock()

    with pytest.mock.patch("httpx.AsyncClient.post", return_value=mock_response):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await usecase._exchange_code("google", "auth_code", "https://example.com/callback")
        assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_exchange_code_github():
    # Setup
    usecase = create_mock_usecase()
    usecase._OAuthUsecase__config_service.GITHUB_CLIENT_ID = "github_client_id"
    usecase._OAuthUsecase__config_service.GITHUB_CLIENT_SECRET = "github_secret"
    usecase._OAuthUsecase__config_service.GITHUB_REDIRECT_URI = (
        "https://example.com/callback"
    )

    # Mock token response
    mock_token_response = Mock()
    mock_token_response.json.return_value = {"access_token": "github_token"}
    mock_token_response.raise_for_status = Mock()

    # Mock user response
    mock_user_response = Mock()
    mock_user_response.json.return_value = {"id": 123, "email": "test@example.com"}
    mock_user_response.raise_for_status = Mock()

    with pytest.mock.patch(
        "httpx.AsyncClient.post", return_value=mock_token_response
    ), pytest.mock.patch("httpx.AsyncClient.get", return_value=mock_user_response):
        # Execute
        result = await usecase._exchange_code("github", "auth_code", "https://example.com/callback")

        # Assert
        assert result["sub"] == "123"
        assert result["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_exchange_code_github_missing_access_token():
    # Setup
    usecase = create_mock_usecase()
    usecase._OAuthUsecase__config_service.GITHUB_CLIENT_ID = "github_client_id"
    usecase._OAuthUsecase__config_service.GITHUB_CLIENT_SECRET = "github_secret"
    usecase._OAuthUsecase__config_service.GITHUB_REDIRECT_URI = (
        "https://example.com/callback"
    )

    # Mock token response without access_token
    mock_response = Mock()
    mock_response.json.return_value = {"token_type": "bearer"}
    mock_response.raise_for_status = Mock()

    with pytest.mock.patch("httpx.AsyncClient.post", return_value=mock_response):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await usecase._exchange_code("github", "auth_code", "https://example.com/callback")
        assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_exchange_code_github_missing_email():
    # Setup
    usecase = create_mock_usecase()
    usecase._OAuthUsecase__config_service.GITHUB_CLIENT_ID = "github_client_id"
    usecase._OAuthUsecase__config_service.GITHUB_CLIENT_SECRET = "github_secret"
    usecase._OAuthUsecase__config_service.GITHUB_REDIRECT_URI = (
        "https://example.com/callback"
    )

    # Mock token response
    mock_token_response = Mock()
    mock_token_response.json.return_value = {"access_token": "github_token"}
    mock_token_response.raise_for_status = Mock()

    # Mock user response without email
    mock_user_response = Mock()
    mock_user_response.json.return_value = {"id": 123}  # Missing email
    mock_user_response.raise_for_status = Mock()
    
    # Mock emails response with empty list
    mock_emails_response = Mock()
    mock_emails_response.json.return_value = []  # No emails found
    mock_emails_response.raise_for_status = Mock()

    with pytest.mock.patch(
        "httpx.AsyncClient.post", return_value=mock_token_response
    ), pytest.mock.patch("httpx.AsyncClient.get", side_effect=[mock_user_response, mock_emails_response]):
        # Execute - this should not raise an exception, just return None for email
        result = await usecase._exchange_code("github", "auth_code", "https://example.com/callback")
        
        # Assert
        assert result["sub"] == "123"
        assert result["email"] is None


@pytest.mark.asyncio
async def test_exchange_code_unsupported_provider():
    # Setup
    usecase = create_mock_usecase()

    # Execute and Assert
    with pytest.raises(ValueError) as excinfo:
        await usecase._exchange_code("unsupported", "auth_code", "https://example.com/callback")
    assert "Unsupported provider" in str(excinfo.value)
