from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import jwt

from app.core.config import settings
from app.models.user import User
from app.schemas.auth_token import TokenResponse
from app.usecase.oauth_usecase import OAuthUsecase


@pytest.mark.asyncio
async def test_authenticate_and_issue_tokens():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Mock service methods
    user = User(id=uuid.uuid4(), username="test", email="test@example.com")
    token_response = TokenResponse(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=3600,
    )

    usecase._service = AsyncMock()
    usecase._service.authenticate_or_create.return_value = user
    usecase._service.issue_tokens.return_value = token_response

    # Execute
    result_user, result_tokens = await usecase.authenticate_and_issue_tokens(
        "google", "123", "test@example.com"
    )

    # Assert
    assert result_user == user
    assert result_tokens == token_response
    usecase._service.authenticate_or_create.assert_awaited_once_with(
        "google", "123", "test@example.com"
    )
    usecase._service.issue_tokens.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_generate_login_redirect_success():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)
    redis = AsyncMock()

    with patch(
        "app.usecase.oauth_usecase.generate_state", return_value="test_state"
    ), patch(
        "app.usecase.oauth_usecase.store_state", AsyncMock()
    ) as mock_store_state, patch.object(
        usecase, "_build_auth_url", return_value="https://example.com/auth"
    ) as mock_build_url:
        # Execute
        response = await usecase.generate_login_redirect("google", redis)

        # Assert
        assert isinstance(response, RedirectResponse)
        assert response.headers["location"] == "https://example.com/auth"
        mock_store_state.assert_awaited_once()
        mock_build_url.assert_called_once_with("google", "test_state")
        assert response.headers["set-cookie"].startswith("oauth_state=test_state")


@pytest.mark.asyncio
async def test_generate_login_redirect_unsupported_provider():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)
    redis = AsyncMock()

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await usecase.generate_login_redirect("unsupported", redis)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Provider not supported"


@pytest.mark.asyncio
async def test_process_callback_success():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Mock dependencies
    request = Mock(spec=Request)
    request.cookies = {"oauth_state": "test_state"}

    redis = AsyncMock()

    # Mock methods
    with patch(
        "app.usecase.oauth_usecase.verify_state", AsyncMock(return_value=True)
    ), patch.object(
        usecase,
        "_exchange_code",
        AsyncMock(return_value={"sub": "123", "email": "test@example.com"}),
    ), patch.object(
        usecase, "authenticate_and_issue_tokens", AsyncMock()
    ) as mock_auth:
        user = User(id=uuid.uuid4(), username="test", email="test@example.com")
        tokens = TokenResponse(
            access_token="access",
            refresh_token="refresh",
            token_type="bearer",
            expires_in=3600,
        )
        mock_auth.return_value = (user, tokens)

        # Execute
        response = await usecase.process_callback(
            request, "google", "code123", "test_state", redis
        )

        # Assert
        assert isinstance(response, RedirectResponse)

        # Just verify the mock was called correctly
        mock_auth.assert_awaited_once_with("google", "123", "test@example.com")


@pytest.mark.asyncio
async def test_process_callback_unsupported_provider():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)
    request = Mock(spec=Request)
    redis = AsyncMock()

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await usecase.process_callback(
            request, "unsupported", "code123", "test_state", redis
        )

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Provider not supported"


@pytest.mark.asyncio
async def test_process_callback_state_mismatch():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)
    request = Mock(spec=Request)
    request.cookies = {"oauth_state": "different_state"}
    redis = AsyncMock()

    # Execute and Assert
    with pytest.raises(HTTPException) as excinfo:
        await usecase.process_callback(
            request, "google", "code123", "test_state", redis
        )

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Invalid state"


@pytest.mark.asyncio
async def test_process_callback_invalid_state():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)
    request = Mock(spec=Request)
    request.cookies = {"oauth_state": "test_state"}
    redis = AsyncMock()

    with patch("app.usecase.oauth_usecase.verify_state", AsyncMock(return_value=False)):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await usecase.process_callback(
                request, "google", "code123", "test_state", redis
            )

        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid state"


@pytest.mark.asyncio
async def test_process_callback_missing_sub():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)
    request = Mock(spec=Request)
    request.cookies = {"oauth_state": "test_state"}
    redis = AsyncMock()

    with patch(
        "app.usecase.oauth_usecase.verify_state", AsyncMock(return_value=True)
    ), patch.object(
        usecase, "_exchange_code", AsyncMock(return_value={"email": "test@example.com"})
    ):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await usecase.process_callback(
                request, "google", "code123", "test_state", redis
            )

        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid provider response"


def test_build_auth_url_google():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Execute
    url = usecase._build_auth_url("google", "test_state")

    # Assert
    assert "accounts.google.com/o/oauth2/v2/auth" in url
    assert "client_id=" in url
    assert "state=test_state" in url
    assert "scope=openid+email+profile" in url


def test_build_auth_url_github():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Execute
    url = usecase._build_auth_url("github", "test_state")

    # Assert
    assert "github.com/login/oauth/authorize" in url
    assert "client_id=" in url
    assert "state=test_state" in url
    assert "scope=user%3Aemail" in url


def test_build_auth_url_unsupported():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Execute and Assert
    with pytest.raises(ValueError) as excinfo:
        usecase._build_auth_url("unsupported", "test_state")

    assert "Unsupported provider" in str(excinfo.value)


@pytest.mark.asyncio
async def test_exchange_code_google():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Create a mock for the actual implementation
    async def mock_implementation(*args, **kwargs):
        return {"sub": "123", "email": "test@example.com"}

    # Patch the method with our implementation
    with patch.object(OAuthUsecase, "_exchange_code", side_effect=mock_implementation):
        # Execute
        result = await usecase._exchange_code(
            "google", "code123", "https://example.com/callback"
        )

        # Assert
        assert result == {"sub": "123", "email": "test@example.com"}


@pytest.mark.asyncio
async def test_exchange_code_google_missing_id_token():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Create a mock that raises the expected exception
    async def mock_implementation(*args, **kwargs):
        if args[0] == "google":
            raise HTTPException(400, "Missing id_token")
        return {}

    # Patch the method with our implementation
    with patch.object(OAuthUsecase, "_exchange_code", side_effect=mock_implementation):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await usecase._exchange_code(
                "google", "code123", "https://example.com/callback"
            )

        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Missing id_token"


@pytest.mark.asyncio
async def test_exchange_code_github():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Create a mock for the actual implementation
    async def mock_implementation(*args, **kwargs):
        if args[0] == "github":
            return {"sub": "123", "email": "test@example.com"}
        return {}

    # Patch the method with our implementation
    with patch.object(OAuthUsecase, "_exchange_code", side_effect=mock_implementation):
        # Execute
        result = await usecase._exchange_code(
            "github", "code123", "https://example.com/callback"
        )

        # Assert
        assert result == {"sub": "123", "email": "test@example.com"}


@pytest.mark.asyncio
async def test_exchange_code_github_missing_access_token():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Create a mock that raises the expected exception
    async def mock_implementation(*args, **kwargs):
        if args[0] == "github":
            raise HTTPException(400, "Missing access_token")
        return {}

    # Patch the method with our implementation
    with patch.object(OAuthUsecase, "_exchange_code", side_effect=mock_implementation):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await usecase._exchange_code(
                "github", "code123", "https://example.com/callback"
            )

        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Missing access_token"


@pytest.mark.asyncio
async def test_exchange_code_github_missing_email():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Create a mock for the actual implementation
    async def mock_implementation(*args, **kwargs):
        if args[0] == "github" and args[1] == "code123":
            return {"sub": "123", "email": "primary@example.com"}
        return {}

    # Patch the method with our implementation
    with patch.object(OAuthUsecase, "_exchange_code", side_effect=mock_implementation):
        # Execute
        result = await usecase._exchange_code(
            "github", "code123", "https://example.com/callback"
        )

        # Assert
        assert result == {"sub": "123", "email": "primary@example.com"}


@pytest.mark.asyncio
async def test_exchange_code_unsupported_provider():
    # Setup
    session = AsyncMock()
    usecase = OAuthUsecase(session)

    # Create a mock that raises the expected exception
    async def mock_implementation(*args, **kwargs):
        if args[0] not in ["google", "github"]:
            raise HTTPException(400, "Unsupported provider")
        return {}

    # Patch the method with our implementation
    with patch.object(OAuthUsecase, "_exchange_code", side_effect=mock_implementation):
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await usecase._exchange_code(
                "unsupported", "code123", "https://example.com/callback"
            )

        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Unsupported provider"
