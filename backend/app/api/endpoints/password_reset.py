from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
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
    db: AsyncSession = Depends(get_db),
) -> Response:
    identifier = payload.email.lower()
    if not reset_rate_limiter.allow(identifier):
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
    await service.send_password_reset(user.email, reset_link)
    Audit.info("password_reset_requested", user_id=user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-reset-token")
async def verify_reset_token(
    payload: PasswordResetVerify,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    repo = PasswordResetRepository(db)
    valid = await repo.get_valid(payload.token) is not None
    return {"valid": valid}


@router.post("/reset-password")
async def reset_password(
    payload: PasswordResetComplete,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    repo = PasswordResetRepository(db)
    pr = await repo.get_valid(payload.token)
    if not pr:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(pr.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    from app.utils.security import PasswordHasher

    user.hashed_password = PasswordHasher.hash_password(payload.password)
    await db.commit()

    await repo.mark_used(pr)

    Audit.info("password_reset_completed", user_id=user.id)
    return {"status": "success"}
