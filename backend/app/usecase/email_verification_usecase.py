from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import BackgroundTasks, HTTPException
from jose import jwt as jose_jwt

from app.core.config import ConfigurationService
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
    """Email verification usecase with explicit dependency injection."""

    def __init__(
        self,
        ev_repo: EmailVerificationRepository,
        user_repo: UserRepository,
        rt_repo: RefreshTokenRepository,
        email_service: EmailService,
        jwt_utils: JWTUtils,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        self.__ev_repo = ev_repo
        self.__user_repo = user_repo
        self.__rt_repo = rt_repo
        self.__email_service = email_service
        self.__jwt_utils = jwt_utils
        self.__config_service = config_service
        self.__audit = audit

    async def verify_email(self, token: str) -> TokenResponse:
        """Validate *token*, mark user as verified and issue JWT tokens."""
        self.__audit.info(
            "verify_email_started",
            token=token[:8] + "..." if len(token) > 8 else token,
        )

        try:
            token_obj = await self.__ev_repo.get_valid(token)
            if not token_obj:
                self.__audit.warning("invalid_email_verification_token")
                raise HTTPException(status_code=400, detail="Invalid or expired token")

            user: Optional[User] = await self.__user_repo.get_by_id(token_obj.user_id)
            if not user:
                self.__audit.error(
                    "user_not_found_for_verification", user_id=str(token_obj.user_id)
                )
                raise HTTPException(status_code=400, detail="User not found")

            user.email_verified = True
            await self.__ev_repo.mark_used(token_obj)

            # Build claims
            additional_claims = {
                "roles": user.roles
                if user.roles
                else [UserRole.INDIVIDUAL_INVESTOR.value],
                "attributes": user.attributes if user.attributes else {},
            }

            access_token = self.__jwt_utils.create_access_token(
                str(user.id), additional_claims=additional_claims
            )
            refresh_token = self.__jwt_utils.create_refresh_token(str(user.id))

            # Persist refresh token JTI hash
            payload_claims = jose_jwt.get_unverified_claims(refresh_token)
            jti = payload_claims["jti"]
            ttl = timedelta(days=self.__config_service.REFRESH_TOKEN_EXPIRE_DAYS)
            await self.__rt_repo.create_from_jti(jti, user.id, ttl)

            self.__audit.info("email_verification_success", user_id=str(user.id))

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=self.__config_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )
        except Exception as e:
            self.__audit.error("email_verification_failed", error=str(e))
            raise

    async def resend_verification(
        self,
        email: str,
        background_tasks: BackgroundTasks,
        rate_limiter: InMemoryRateLimiter,
    ) -> None:
        """Generate a new token and send verification email if allowed."""
        self.__audit.info("resend_verification_started", email=email)

        try:
            identifier = email.lower()
            if not rate_limiter.allow(identifier):
                self.__audit.error("email_verification_rate_limited", email=email)
                raise HTTPException(status_code=429, detail="Too many requests")

            user = await self.__user_repo.get_by_email(email)
            if not user or user.email_verified:
                self.__audit.warning(
                    "verification_email_resend_unknown_or_verified", email=email
                )
                return  # Silently succeed for idempotency

            token, _, expires_at = generate_verification_token()
            await self.__ev_repo.create(token, user.id, expires_at)

            frontend_base_url = self.__config_service.FRONTEND_BASE_URL.rstrip("/")
            verify_link = f"{frontend_base_url}/verify-email?token={token}"

            background_tasks.add_task(
                self.__email_service.send_email_verification, user.email, verify_link
            )

            self.__audit.info("verification_email_resent", user_id=str(user.id))
        except Exception as e:
            self.__audit.error("resend_verification_failed", email=email, error=str(e))
            raise
