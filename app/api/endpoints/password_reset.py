from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, status

from app.core.config import Configuration
from app.domain.schemas.password_reset import (
    PasswordResetComplete,
    PasswordResetRequest,
    PasswordResetVerify,
)
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.utils.logging import Audit
from app.utils.rate_limiter import RateLimiterUtils
from app.utils.security import PasswordHasher
from app.utils.token import generate_token


class PasswordReset:
    """Password reset endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(prefix="/auth", tags=["auth"])
    __password_reset_repo: PasswordResetRepository
    __user_repo: UserRepository
    __email_service: EmailService
    __rate_limiter_utils: RateLimiterUtils
    __password_hasher: PasswordHasher
    __config: Configuration

    def __init__(
        self,
        password_reset_repository: PasswordResetRepository,
        user_repository: UserRepository,
        email_service: EmailService,
        rate_limiter_utils: RateLimiterUtils,
        password_hasher: PasswordHasher,
        config: Configuration,
    ):
        """Initialize with injected dependencies."""
        PasswordReset.__password_reset_repo = password_reset_repository
        PasswordReset.__user_repo = user_repository
        PasswordReset.__email_service = email_service
        PasswordReset.__rate_limiter_utils = rate_limiter_utils
        PasswordReset.__password_hasher = password_hasher
        PasswordReset.__config = config

    @staticmethod
    @ep.post(
        "/password-reset-request",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        response_model=None,
    )
    async def request_password_reset(
        payload: PasswordResetRequest,
        background_tasks: BackgroundTasks,
    ) -> Response:
        """Request a password reset."""
        # Check rate limiting
        if not PasswordReset.__rate_limiter_utils.login_rate_limiter.allow(
            payload.email
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset requests. Please try again later.",
            )

        # Find user by email
        user = await PasswordReset.__user_repo.get_by_email(payload.email)
        if not user:
            # Don't reveal whether email exists - return success anyway
            Audit.warning(
                "Password reset requested for non-existent email", email=payload.email
            )
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        # Generate reset token (expires in 30 minutes)
        token, _, expires_at = generate_token(expiration_minutes=30)

        # Save reset token to database
        await PasswordReset.__password_reset_repo.create(token, user.id, expires_at)

        # Build reset link
        frontend_url = (
            PasswordReset.__config.FRONTEND_BASE_URL or "http://localhost:3000"
        )
        reset_link = f"{frontend_url}/reset-password?token={token}"

        # Send email with reset token
        background_tasks.add_task(
            PasswordReset.__email_service.send_password_reset, user.email, reset_link
        )

        Audit.info(
            "Password reset email sent", email=payload.email, user_id=str(user.id)
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @staticmethod
    @ep.post("/password-reset-verify")
    async def verify_password_reset(payload: PasswordResetVerify):
        """Verify password reset token."""
        reset_record = await PasswordReset.__password_reset_repo.get_valid(
            payload.token
        )
        if not reset_record:
            Audit.warning(
                "Password reset token verification failed",
                token=payload.token[:8] + "...",
            )
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        Audit.info(
            "Password reset token verified",
            token=payload.token[:8] + "...",
            user_id=str(reset_record.user_id),
        )
        return {"valid": True, "message": "Token verified"}

    @staticmethod
    @ep.post("/password-reset-complete")
    async def complete_password_reset(payload: PasswordResetComplete):
        """Complete password reset with new password."""
        reset_record = await PasswordReset.__password_reset_repo.get_valid(
            payload.token
        )
        if not reset_record:
            Audit.warning(
                "Password reset completion failed - invalid token",
                token=payload.token[:8] + "...",
            )
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user = await PasswordReset.__user_repo.get_by_id(reset_record.user_id)
        if not user:
            Audit.error(
                "Password reset completion failed - user not found",
                user_id=str(reset_record.user_id),
            )
            raise HTTPException(status_code=400, detail="User not found")

        # Update password
        hashed_password = PasswordReset.__password_hasher.hash_password(
            payload.password
        )
        await PasswordReset.__user_repo.update(user, hashed_password=hashed_password)

        # Mark reset token as used
        await PasswordReset.__password_reset_repo.mark_used(reset_record)

        Audit.info(
            "Password reset completed",
            token=payload.token[:8] + "...",
            user_id=str(user.id),
        )
        return {"message": "Password reset completed successfully"}
