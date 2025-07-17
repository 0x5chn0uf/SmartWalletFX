from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Response, status

from app.domain.schemas.auth_token import TokenResponse
from app.domain.schemas.email_verification import (
    EmailVerificationRequest,
    EmailVerificationVerify,
)
from app.usecase.email_verification_usecase import EmailVerificationUsecase
from app.utils.rate_limiter import InMemoryRateLimiter

verify_rate_limiter = InMemoryRateLimiter(max_attempts=5, window_seconds=3600)


class EmailVerification:
    """Email verification endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(prefix="/auth", tags=["auth"])
    __verification_uc: EmailVerificationUsecase

    def __init__(self, verification_usecase: EmailVerificationUsecase):
        """Initialize with injected dependencies."""
        EmailVerification.__verification_uc = verification_usecase

    @staticmethod
    @ep.post("/verify-email", response_model=TokenResponse)
    async def verify_email(payload: EmailVerificationVerify):
        """Verify email using verification token."""
        return await EmailVerification.__verification_uc.verify_email(payload.token)

    @staticmethod
    @ep.post(
        "/resend-verification",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        response_model=None,
    )
    async def resend_verification_email(
        payload: EmailVerificationRequest,
        background_tasks: BackgroundTasks,
    ) -> Response:
        """Resend verification email."""
        await EmailVerification.__verification_uc.resend_verification(
            payload.email, background_tasks, verify_rate_limiter
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
