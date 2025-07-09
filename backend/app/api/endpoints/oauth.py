from __future__ import annotations

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_redis
from app.core.config import settings
from app.services.oauth_service import OAuthService
from app.utils.logging import Audit
from app.utils.oauth_state_cache import (
    generate_state,
    store_state,
    verify_state,
)

router = APIRouter(prefix="/auth/oauth", tags=["auth"])


PROVIDERS = {"google", "github"}


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


@router.get("/{provider}/login")
async def oauth_login(
    provider: str,
    redis=Depends(get_redis),
) -> RedirectResponse:
    if provider not in PROVIDERS:
        Audit.error("oauth_unknown_provider", provider=provider)
        raise HTTPException(status_code=404, detail="Provider not supported")

    state = generate_state()
    await store_state(redis, state)

    url = _build_auth_url(provider, state)
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


async def _exchange_code(provider: str, code: str, redirect_uri: str) -> dict[str, str]:
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


@router.get("/{provider}/callback")
async def oauth_callback(
    request: Request,
    provider: str,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> Response:
    Audit.info("oauth_callback_start", provider=provider)

    if provider not in PROVIDERS:
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
    user_info = await _exchange_code(provider, code, redirect_uri)
    if not user_info.get("sub"):
        Audit.error("oauth_missing_sub", provider=provider)
        raise HTTPException(400, "Invalid provider response")

    service = OAuthService(db)
    user = await service.authenticate_or_create(
        provider, user_info["sub"], user_info.get("email")
    )
    tokens = await service.issue_tokens(user)
    Audit.info("oauth_login_success", provider=provider, user_id=str(user.id))

    # Redirect browser to frontend /defi route
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
