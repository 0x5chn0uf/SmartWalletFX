from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth_token import TokenResponse
from app.schemas.email_verification import (
    EmailVerificationRequest,
    EmailVerificationVerify,
)
from app.usecase.email_verification_usecase import EmailVerificationUsecase
from app.utils.rate_limiter import InMemoryRateLimiter

router = APIRouter(prefix="/auth")

verify_rate_limiter = InMemoryRateLimiter(max_attempts=5, window_seconds=3600)


@router.post(
    "/verify-email",
    response_model=TokenResponse,
)
async def verify_email(
    payload: EmailVerificationVerify, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    usecase = EmailVerificationUsecase(db)
    return await usecase.verify_email(payload.token)


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
    usecase = EmailVerificationUsecase(db)
    await usecase.resend_verification(
        payload.email, background_tasks, verify_rate_limiter
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
