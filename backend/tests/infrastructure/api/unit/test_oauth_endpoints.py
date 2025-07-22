from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse, Response

from app.api.endpoints.oauth import OAuth
from app.usecase.oauth_usecase import OAuthUsecase


class TestOAuthEndpoints:
    """Test OAuth endpoints."""

    def test_oauth_init(self):
        """Test OAuth initialization."""
        mock_usecase = Mock(spec=OAuthUsecase)
        OAuth(mock_usecase)
        assert OAuth._OAuth__oauth_uc is mock_usecase

    @pytest.mark.asyncio
    async def test_oauth_login_success(self):
        """Test successful OAuth login redirect."""
        mock_usecase = Mock(spec=OAuthUsecase)
        mock_usecase.generate_login_redirect = AsyncMock(
            return_value=RedirectResponse(url="https://example.com/auth")
        )

        OAuth(mock_usecase)
        mock_redis = Mock()

        result = await OAuth.oauth_login("google", mock_redis)

        assert isinstance(result, RedirectResponse)
        assert result.headers["location"] == "https://example.com/auth"
        mock_usecase.generate_login_redirect.assert_called_once_with(
            "google", mock_redis
        )

    @pytest.mark.asyncio
    async def test_oauth_callback_success(self):
        """Test successful OAuth callback."""
        mock_usecase = Mock(spec=OAuthUsecase)
        mock_response = Response(content="success", status_code=200)
        mock_usecase.process_callback = AsyncMock(return_value=mock_response)

        OAuth(mock_usecase)

        request = Mock(spec=Request)
        request.cookies = {"oauth_state": "test_state"}
        mock_redis = Mock()

        with patch("app.api.endpoints.oauth.verify_state", return_value=True):
            result = await OAuth.oauth_callback(
                request, "google", "test_code", "test_state", mock_redis
            )

        assert result is mock_response
        mock_usecase.process_callback.assert_called_once_with(
            request, "google", "test_code", "test_state", mock_redis
        )

    @pytest.mark.asyncio
    async def test_oauth_callback_unsupported_provider(self):
        """Test OAuth callback with unsupported provider."""
        mock_usecase = Mock(spec=OAuthUsecase)
        OAuth(mock_usecase)

        request = Mock(spec=Request)
        request.cookies = {"oauth_state": "test_state"}
        mock_redis = Mock()

        with pytest.raises(HTTPException) as exc:
            await OAuth.oauth_callback(
                request, "unsupported", "test_code", "test_state", mock_redis
            )

        assert exc.value.status_code == 404
        assert "Provider not supported" in exc.value.detail

    @pytest.mark.asyncio
    async def test_oauth_callback_no_cookie_state(self):
        """Test OAuth callback with no cookie state."""
        mock_usecase = Mock(spec=OAuthUsecase)
        OAuth(mock_usecase)

        request = Mock(spec=Request)
        request.cookies = {}
        mock_redis = Mock()

        with pytest.raises(HTTPException) as exc:
            await OAuth.oauth_callback(
                request, "google", "test_code", "test_state", mock_redis
            )

        assert exc.value.status_code == 400
        assert "Invalid state" in exc.value.detail

    @pytest.mark.asyncio
    async def test_oauth_callback_state_mismatch(self):
        """Test OAuth callback with state mismatch."""
        mock_usecase = Mock(spec=OAuthUsecase)
        OAuth(mock_usecase)

        request = Mock(spec=Request)
        request.cookies = {"oauth_state": "cookie_state"}
        mock_redis = Mock()

        with pytest.raises(HTTPException) as exc:
            await OAuth.oauth_callback(
                request, "google", "test_code", "different_state", mock_redis
            )

        assert exc.value.status_code == 400
        assert "Invalid state" in exc.value.detail

    @pytest.mark.asyncio
    async def test_oauth_callback_invalid_state_verification(self):
        """Test OAuth callback with invalid state verification."""
        mock_usecase = Mock(spec=OAuthUsecase)
        OAuth(mock_usecase)

        request = Mock(spec=Request)
        request.cookies = {"oauth_state": "test_state"}
        mock_redis = Mock()

        with patch("app.api.endpoints.oauth.verify_state", return_value=False):
            with pytest.raises(HTTPException) as exc:
                await OAuth.oauth_callback(
                    request, "google", "test_code", "test_state", mock_redis
                )

        assert exc.value.status_code == 400
        assert "Invalid state" in exc.value.detail

    @pytest.mark.asyncio
    async def test_oauth_callback_github_provider(self):
        """Test OAuth callback with GitHub provider."""
        mock_usecase = Mock(spec=OAuthUsecase)
        mock_response = Response(content="success", status_code=200)
        mock_usecase.process_callback = AsyncMock(return_value=mock_response)

        OAuth(mock_usecase)

        request = Mock(spec=Request)
        request.cookies = {"oauth_state": "test_state"}
        mock_redis = Mock()

        with patch("app.api.endpoints.oauth.verify_state", return_value=True):
            result = await OAuth.oauth_callback(
                request, "github", "test_code", "test_state", mock_redis
            )

        assert result is mock_response
        mock_usecase.process_callback.assert_called_once_with(
            request, "github", "test_code", "test_state", mock_redis
        )
