from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.email_verification_repository import EmailVerificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.email_verification import EmailVerificationRequest, EmailVerificationVerify
from app.services.email_service import EmailService
from app.utils.logging import Audit
from app.utils.rate_limiter import InMemoryRateLimiter
from app.utils.token import generate_verification_token

router = APIRouter(prefix="/auth")

verify_rate_limiter = InMemoryRateLimiter(max_attempts=5, window_seconds=3600)


@router.post(
    "/verify-email",
    response_model=dict,
)
async def verify_email(
    payload: EmailVerificationVerify, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    repo = EmailVerificationRepository(db)
    token_obj = await repo.get_valid(payload.token)
    if not token_obj:
        Audit.error("invalid_email_verification_token")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(token_obj.user_id)
    if not user:
        Audit.error("user_not_found_for_verification", user_id=str(token_obj.user_id))
        raise HTTPException(status_code=400, detail="User not found")

    user.email_verified = True
    await repo.mark_used(token_obj)
    await db.commit()

    Audit.info("email_verified", user_id=str(user.id))
    return {"status": "verified"}


@router.post(
    "/resend-verification",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def resend_verification_email(
    payload: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Response:
    identifier = payload.email.lower()
    if not verify_rate_limiter.allow(identifier):
        Audit.error("email_verification_rate_limited", email=payload.email)
        raise HTTPException(status_code=429, detail="Too many requests")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(payload.email)
    if not user or user.email_verified:
        Audit.warning("verification_email_resend_unknown_or_verified", email=payload.email)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    token, _, expires_at = generate_verification_token()
    ev_repo = EmailVerificationRepository(db)
    await ev_repo.create(token, user.id, expires_at)

    verify_link = f"https://example.com/verify-email?token={token}"
    service = EmailService()
    try:
        background_tasks.add_task(service.send_email_verification, user.email, verify_link)
    except Exception as exc:  # pragma: no cover - network errors aren't common
        Audit.error("verification_email_send_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Email send failed")

    Audit.info("verification_email_resent", user_id=str(user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
