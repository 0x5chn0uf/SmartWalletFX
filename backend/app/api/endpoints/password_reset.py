from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.password_reset import (
    PasswordResetComplete,
    PasswordResetRequest,
    PasswordResetVerify,
)
from app.services.email_service import EmailService
from app.utils.logging import Audit
from app.utils.rate_limiter import InMemoryRateLimiter
from app.utils.token import generate_token

router = APIRouter(prefix="/auth")

reset_rate_limiter = InMemoryRateLimiter(max_attempts=5, window_seconds=3600)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def request_password_reset(
    payload: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Response:
    identifier = payload.email.lower()
    if not reset_rate_limiter.allow(identifier):
        Audit.error("password_reset_rate_limited", email=payload.email)
        raise HTTPException(status_code=429, detail="Too many requests")

    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)
    if not user:
        Audit.warning("password_reset_requested_unknown_email", email=payload.email)
        return

    token, token_hash, expires_at = generate_token()
    pr_repo = PasswordResetRepository(db)
    await pr_repo.create(token, user.id, expires_at)

    reset_link = f"https://example.com/reset-password?token={token}"
    service = EmailService()
    try:
        background_tasks.add_task(service.send_password_reset, user.email, reset_link)
    except Exception as exc:  # pragma: no cover - network errors aren't common
        Audit.error("password_reset_email_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Email send failed")
    Audit.info("password_reset_requested", user_id=user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-reset-token")
async def verify_reset_token(
    payload: PasswordResetVerify,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    repo = PasswordResetRepository(db)
    valid = await repo.get_valid(payload.token) is not None
    Audit.info("password_reset_token_verification", valid=valid)
    return {"valid": valid}


@router.post("/reset-password")
async def reset_password(
    payload: PasswordResetComplete,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    repo = PasswordResetRepository(db)
    pr = await repo.get_valid(payload.token)
    if not pr:
        Audit.error("password_reset_invalid_token")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(pr.user_id)
    if not user:
        Audit.error("password_reset_user_not_found", user_id=str(pr.user_id))
        raise HTTPException(status_code=400, detail="User not found")

    from app.utils.security import PasswordHasher

    user.hashed_password = PasswordHasher.hash_password(payload.password)
    await db.commit()

    await repo.mark_used(pr)

    Audit.info("password_reset_completed", user_id=user.id)
    return {"status": "success"}
