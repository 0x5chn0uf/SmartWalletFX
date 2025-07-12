from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import BackgroundTasks, HTTPException
from jose import jwt as jose_jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security.roles import UserRole
from app.models.user import User
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_token import TokenResponse
from app.services.email_service import EmailService
from app.utils.jwt import JWTUtils
from app.utils.logging import Audit
from app.utils.rate_limiter import InMemoryRateLimiter
from app.utils.token import generate_verification_token


class EmailVerificationUsecase:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._ev_repo = EmailVerificationRepository(session)
        self._user_repo = UserRepository(session)
        self._rt_repo = RefreshTokenRepository(session)

    async def verify_email(self, token: str) -> TokenResponse:
        """Validate *token*, mark user as verified and issue JWT tokens."""
        token_obj = await self._ev_repo.get_valid(token)
        if not token_obj:
            Audit.error("invalid_email_verification_token")
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user: Optional[User] = await self._user_repo.get_by_id(token_obj.user_id)
        if not user:
            Audit.error(
                "user_not_found_for_verification", user_id=str(token_obj.user_id)
            )
            raise HTTPException(status_code=400, detail="User not found")

        user.email_verified = True
        await self._ev_repo.mark_used(token_obj)

        # Build claims
        additional_claims = {
            "roles": user.roles if user.roles else [UserRole.INDIVIDUAL_INVESTOR.value],
            "attributes": user.attributes if user.attributes else {},
        }

        access_token = JWTUtils.create_access_token(
            str(user.id), additional_claims=additional_claims
        )
        refresh_token = JWTUtils.create_refresh_token(str(user.id))

        # Persist refresh token JTI hash
        payload_claims = jose_jwt.get_unverified_claims(refresh_token)
        jti = payload_claims["jti"]
        ttl = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._rt_repo.create_from_jti(jti, user.id, ttl)

        await self._session.commit()

        Audit.info("email_verified", user_id=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def resend_verification(
        self,
        email: str,
        background_tasks: BackgroundTasks,
        rate_limiter: InMemoryRateLimiter,
    ) -> None:
        """Generate a new token and send verification email if allowed."""

        identifier = email.lower()
        if not rate_limiter.allow(identifier):
            Audit.error("email_verification_rate_limited", email=email)
            raise HTTPException(status_code=429, detail="Too many requests")

        user = await self._user_repo.get_by_email(email)
        if not user or user.email_verified:
            Audit.warning("verification_email_resend_unknown_or_verified", email=email)
            return  # Silently succeed for idempotency

        token, _, expires_at = generate_verification_token()
        await self._ev_repo.create(token, user.id, expires_at)

        verify_link = (
            f"{settings.FRONTEND_BASE_URL.rstrip('/')}/verify-email?token={token}"
        )
        service = EmailService()
        background_tasks.add_task(
            service.send_email_verification, user.email, verify_link
        )

        Audit.info("verification_email_resent", user_id=str(user.id))
