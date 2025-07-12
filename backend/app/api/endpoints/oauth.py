from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_redis
from app.usecase.oauth_usecase import OAuthUsecase
from app.utils.logging import Audit
from app.utils.oauth_state_cache import verify_state

router = APIRouter(prefix="/auth/oauth", tags=["auth"])


@router.get("/{provider}/login")
async def oauth_login(
    provider: str,
    redis=Depends(get_redis),
) -> RedirectResponse:
    usecase = OAuthUsecase(None)  # session not needed for login
    return await usecase.generate_login_redirect(provider, redis)


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

    if provider not in {"google", "github"}:
        Audit.error("oauth_unknown_provider", provider=provider)
        raise HTTPException(status_code=404, detail="Provider not supported")

    cookie_state = request.cookies.get("oauth_state")

    if not cookie_state or state != cookie_state:
        Audit.error("oauth_state_mismatch", provider=provider)
        raise HTTPException(status_code=400, detail="Invalid state")

    if not await verify_state(redis, state):
        Audit.error("oauth_state_invalid", provider=provider)
        raise HTTPException(status_code=400, detail="Invalid state")

    usecase = OAuthUsecase(db)
    return await usecase.process_callback(request, provider, code, state, redis)
