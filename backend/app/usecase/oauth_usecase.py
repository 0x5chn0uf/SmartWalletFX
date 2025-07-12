from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.schemas.auth_token import TokenResponse
from app.services.oauth_service import OAuthService
from app.utils.logging import Audit
from app.utils.oauth_state_cache import (
    generate_state,
    store_state,
    verify_state,
)


class OAuthUsecase:
    """Use case wrapping OAuthService to keep endpoints thin."""

    _PROVIDERS = {"google", "github"}

    def __init__(self, session: AsyncSession) -> None:
        self._service = OAuthService(session)

    async def authenticate_and_issue_tokens(
        self, provider: str, sub: str, email: Optional[str] | None
    ) -> tuple[User, TokenResponse]:
        """Authenticate via provider's account and return user + JWT tokens."""
        user = await self._service.authenticate_or_create(provider, sub, email)
        tokens = await self._service.issue_tokens(user)
        return user, tokens

    async def generate_login_redirect(self, provider: str, redis) -> RedirectResponse:
        """Return RedirectResponse that sends the browser to the provider login page."""

        if provider not in self._PROVIDERS:
            Audit.error("oauth_unknown_provider", provider=provider)
            raise HTTPException(status_code=404, detail="Provider not supported")

        state = generate_state()
        await store_state(redis, state)

        url = self._build_auth_url(provider, state)
        resp = RedirectResponse(url)

        resp.set_cookie(
            "oauth_state",
            state,
            max_age=300,
            httponly=True,
            samesite="lax",
            secure=settings.ENVIRONMENT.lower() == "production",
        )

        Audit.info("oauth_login_url_generated", provider=provider)
        return resp

    async def process_callback(
        self,
        request: Request,
        provider: str,
        code: str,
        state: str,
        redis,
    ) -> RedirectResponse:
        """Handle OAuth provider callback and return redirect to frontend."""

        Audit.info("oauth_callback_start", provider=provider)

        if provider not in self._PROVIDERS:
            Audit.error("oauth_unknown_provider", provider=provider)
            raise HTTPException(status_code=404, detail="Provider not supported")

        cookie_state = request.cookies.get("oauth_state")

        if not cookie_state or state != cookie_state:
            Audit.error("oauth_state_mismatch", provider=provider)
            raise HTTPException(status_code=400, detail="Invalid state")

        if not await verify_state(redis, state):
            Audit.error("oauth_state_invalid", provider=provider)
            raise HTTPException(status_code=400, detail="Invalid state")

        redirect_uri = settings.OAUTH_REDIRECT_URI.format(provider=provider)
        user_info = await self._exchange_code(provider, code, redirect_uri)
        if not user_info.get("sub"):
            Audit.error("oauth_missing_sub", provider=provider)
            raise HTTPException(400, "Invalid provider response")

        user, tokens = await self.authenticate_and_issue_tokens(
            provider, user_info["sub"], user_info.get("email")
        )

        Audit.info("oauth_login_success", provider=provider, user_id=str(user.id))

        front_url = settings.FRONTEND_BASE_URL.rstrip("/") + "/defi"
        resp = RedirectResponse(url=front_url, status_code=302)

        resp.set_cookie(
            "access_token",
            tokens.access_token,
            httponly=True,
            samesite="lax",
        )
        resp.set_cookie(
            "refresh_token",
            tokens.refresh_token,
            httponly=True,
            samesite="lax",
            path="/auth/refresh",
        )

        return resp

    # ---------- Internal helpers ------------------------------------------

    @staticmethod
    def _build_auth_url(provider: str, state: str) -> str:
        if provider == "google":
            params = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "response_type": "code",
                "redirect_uri": settings.OAUTH_REDIRECT_URI.format(provider="google"),
                "scope": "openid email profile",
                "state": state,
                "access_type": "offline",
            }
            return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        if provider == "github":
            params = {
                "client_id": settings.GITHUB_CLIENT_ID,
                "redirect_uri": settings.OAUTH_REDIRECT_URI.format(provider="github"),
                "scope": "user:email",
                "state": state,
            }
            return "https://github.com/login/oauth/authorize?" + urlencode(params)
        Audit.error("oauth_auth_url_unsupported", provider=provider)
        raise ValueError("Unsupported provider")

    @staticmethod
    async def _exchange_code(
        provider: str, code: str, redirect_uri: str
    ) -> dict[str, str]:
        async with httpx.AsyncClient(timeout=10) as client:
            if provider == "google":
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                token_resp.raise_for_status()
                data = token_resp.json()
                id_token = data.get("id_token")
                if not id_token:
                    Audit.error("oauth_missing_id_token", provider=provider)
                    raise HTTPException(400, "Missing id_token")
                from jose import jwt

                claims = jwt.get_unverified_claims(id_token)
                return {"sub": claims.get("sub"), "email": claims.get("email")}
            if provider == "github":
                token_resp = await client.post(
                    "https://github.com/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": settings.GITHUB_CLIENT_ID,
                        "client_secret": settings.GITHUB_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                )
                token_resp.raise_for_status()
                access_token = token_resp.json().get("access_token")
                if not access_token:
                    Audit.error("oauth_missing_access_token", provider=provider)
                    raise HTTPException(400, "Missing access_token")
                user_resp = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {access_token}"},
                )
                user_resp.raise_for_status()
                user = user_resp.json()
                email = user.get("email")
                if not email:
                    emails_resp = await client.get(
                        "https://api.github.com/user/emails",
                        headers={"Authorization": f"token {access_token}"},
                    )
                    emails_resp.raise_for_status()
                    for item in emails_resp.json():
                        if item.get("primary"):
                            email = item.get("email")
                            break
                return {"sub": str(user.get("id")), "email": email}
        Audit.error("oauth_exchange_unsupported_provider", provider=provider)
        raise HTTPException(400, "Unsupported provider")
