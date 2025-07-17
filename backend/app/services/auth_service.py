"""Application-layer authentication service.

Encapsulates business rules for user registration and, in
future, login & token issuance.  Keeping logic here enables
straightforward unit testing and maintains a clean separation between
FastAPI adapters and domain/infrastructure layers.
"""
from __future__ import annotations

from datetime import timedelta
from hashlib import sha256
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.exc import IntegrityError

from app.core.config import ConfigurationService
from app.core.security.roles import UserRole
from app.domain.errors import InvalidCredentialsError
from app.domain.schemas.auth_token import TokenResponse
from app.domain.schemas.user import UserCreate
from app.models.user import User
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.utils import security
from app.utils.jwt import JWTUtils
from app.utils.logging import Audit
from app.utils.token import generate_verification_token


class DuplicateError(Exception):
    """Raised when *username* or *email* is already registered."""

    def __init__(self, field: str):
        super().__init__(field)
        self.field = field


class AuthService:
    """Core authentication service (register, authenticate, tokens…)."""

    def __init__(
        self,
        user_repository: UserRepository,
        email_verification_repository: EmailVerificationRepository,
        refresh_token_repository: RefreshTokenRepository,
        email_service: EmailService,
        jwt_utils: JWTUtils,
        config_service: ConfigurationService,
        audit: Audit,
    ):
        """Initialize with injected dependencies."""
        self.__user_repo = user_repository
        self.__email_verification_repo = email_verification_repository
        self.__refresh_token_repo = refresh_token_repository
        self.__email_service = email_service
        self.__jwt_utils = jwt_utils
        self.__config_service = config_service
        self.__audit = audit

    async def register(  # noqa: D401 – business method
        self,
        payload: UserCreate,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> User:
        """Register a new user.

        Args:
            payload: :class:`UserCreate` schema.

        Returns:
            Newly-persisted :class:`app.models.user.User` object.

        Raises:
            DuplicateError: If provided *username* or *email* already exists.
            WeakPasswordError: If *password* does not meet strength policy.
        """
        # Password strength validation is handled by UserCreate's field validator

        # Duplicate checks
        if await self.__user_repo.get_by_username(payload.username):
            self.__audit.warning("User already exists", username=payload.username)
            raise DuplicateError("username")
        if await self.__user_repo.get_by_email(payload.email):
            self.__audit.warning("User already exists", email=payload.email)
            raise DuplicateError("email")

        hashed_pw = security.get_password_hash(payload.password)

        user = User(
            username=payload.username,
            email=payload.email,
            hashed_password=hashed_pw,
            # Default role for new users
            roles=[UserRole.INDIVIDUAL_INVESTOR.value],
            attributes={},
        )

        try:
            user = await self.__user_repo.save(user)
        except IntegrityError as exc:  # pragma: no cover – safeguard
            # Handle race condition duplicates at DB level
            self.__audit.warning("user_register_integrity_error", error=str(exc.orig))
            if "users_email_key" in str(exc.orig):  # simplistic check
                raise DuplicateError("email") from exc
            raise

        token, _, expires_at = generate_verification_token()
        await self.__email_verification_repo.create(token, user.id, expires_at)

        # Build a portable verification URL based on the configured frontend base
        verify_link = f"{self.__config_service.FRONTEND_BASE_URL.rstrip('/')}/verify-email?token={token}"

        if background_tasks is not None:
            background_tasks.add_task(
                self.__email_service.send_email_verification, user.email, verify_link
            )
        else:  # Fallback – send inline (mainly for tests/CLI)
            await self.__email_service.send_email_verification(user.email, verify_link)

        # Note: Session operations are now handled by the repositories internally

        self.__audit.info("user_registered", extra={"user_id": str(user.id)})
        return user

    async def authenticate(
        self, identity: str, password: str
    ) -> TokenResponse:  # noqa: D401 – business method
        """Verify *identity* (username **or** email) and issue JWTs.

        The check is performed in constant-time regardless of user-existence to
        mitigate timing attacks. Generic domain errors are raised on failure to
        avoid user enumeration.
        """

        from app.domain.errors import (
            InactiveUserError,  # local import to avoid circular deps
        )

        identity_lc = identity.lower().strip()

        # ------------------------------------------------------------------
        # Fetch user by *username* first, fallback to *email* to support both.
        # Username is stored in DB as-is but indexed; we normalise to lowercase
        # for a case-insensitive comparison. Email column is already unique.
        # ------------------------------------------------------------------
        user: User | None = await self.__user_repo.get_by_username(identity_lc)
        if user is None:
            user = await self.__user_repo.get_by_email(identity_lc)

        # ------------------------------------------------------------------
        # Constant-time password verification
        # ------------------------------------------------------------------
        if user is None:
            # Generate a dummy hash once (module-level cache) to keep timing
            # consistent. passlib context handles constant-time comparison.
            from functools import lru_cache

            @lru_cache(maxsize=1)
            def _dummy_hash() -> str:  # pragma: no cover – trivial helper
                return security.PasswordHasher.hash_password("dummypassword123!@#")

            # Constant-time verification against dummy hash to equalise timing
            security.PasswordHasher.verify_password(password, _dummy_hash())
            self.__audit.error(
                "AUTH_FAILURE", reason="invalid_credentials", identity=identity_lc
            )
            raise InvalidCredentialsError()

        if getattr(user, "is_active", True) is False:
            self.__audit.error(
                "AUTH_FAILURE", reason="inactive_account", user_id=str(user.id)
            )
            raise InactiveUserError()

        if not security.PasswordHasher.verify_password(password, user.hashed_password):
            self.__audit.error(
                "AUTH_FAILURE", reason="invalid_credentials", user_id=str(user.id)
            )
            raise InvalidCredentialsError()

        # Reject all logins when the email address is not verified – no grace period
        if not getattr(user, "email_verified", False):
            self.__audit.error(
                "AUTH_FAILURE",
                reason="email_unverified",
                user_id=str(user.id),
            )
            from app.domain.errors import UnverifiedEmailError

            raise UnverifiedEmailError()

        # Prepare additional claims for RBAC/ABAC
        additional_claims = {}

        user_roles = user.roles if user.roles else [UserRole.INDIVIDUAL_INVESTOR.value]
        additional_claims["roles"] = user_roles

        user_attributes = user.attributes if user.attributes else {}
        additional_claims["attributes"] = user_attributes

        # Issue tokens with role/attribute claims
        access_token = self.__jwt_utils.create_access_token(
            str(user.id), additional_claims=additional_claims
        )
        refresh_token = self.__jwt_utils.create_refresh_token(str(user.id))

        # Persist refresh token JTI hash *before* we access any attributes that
        # may expire on commit.  We therefore **stash** the primary-key value
        # so that subsequent logging does not trigger a lazy-load which would
        # perform I/O in the synchronous response thread (leading to the
        # dreaded ``MissingGreenlet`` error seen in the failing test).

        from jose import jwt as jose_jwt  # local import to defer heavy dep

        payload = jose_jwt.get_unverified_claims(refresh_token)
        jti = payload["jti"]
        ttl = timedelta(days=self.__config_service.REFRESH_TOKEN_EXPIRE_DAYS)

        user_pk = user.id  # capture before commit/expiration
        await self.__refresh_token_repo.create_from_jti(jti, user_pk, ttl)

        user_pk_str = str(user_pk)
        self.__audit.info(
            "user_login_success", user_id=user_pk_str, jti=jti, roles=user_roles
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.__config_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Validate *refresh_token* and issue a new access token.

        The refresh token itself remains valid (rotate-at-will pattern).
        Additional role/attribute claims are injected in the new access token
        to mirror the latest user state.
        """

        from hashlib import sha256

        from app.domain.errors import InvalidCredentialsError

        try:
            payload = self.__jwt_utils.decode_token(refresh_token)
        except Exception as exc:  # noqa: BLE001
            self.__audit.error("Invalid decoded token", exc_info=exc)
            raise InvalidCredentialsError() from exc

        if payload.get("type") != "refresh":
            self.__audit.error("Invalid token type", payload=payload)
            raise InvalidCredentialsError()

        user_id = payload.get("sub")
        jti = payload.get("jti")
        if not user_id or not jti:
            self.__audit.error("Invalid token payload", payload=payload)
            raise InvalidCredentialsError()

        # Verify token exists and not revoked/expired in DB
        jti_hash = sha256(jti.encode()).hexdigest()
        token_obj = await self.__refresh_token_repo.get_by_jti_hash(jti_hash)

        if token_obj is None or token_obj.revoked:
            self.__audit.error("Invalid token object", token_obj=token_obj)
            raise InvalidCredentialsError()

        # Fetch user
        user = await self.__user_repo.get_by_id(user_id)
        if user is None:
            self.__audit.error("User not found", user_id=user_id)
            raise InvalidCredentialsError()

        # Build additional claims
        user_roles = user.roles or [UserRole.INDIVIDUAL_INVESTOR.value]
        user_attributes = user.attributes or {}

        self.__audit.info(
            "Building additional claims",
            user_roles=user_roles,
            user_attributes=user_attributes,
        )

        access_token = self.__jwt_utils.create_access_token(
            str(user.id),
            additional_claims={"roles": user_roles, "attributes": user_attributes},
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Same refresh token returned
            token_type="bearer",
            expires_in=self.__config_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revoke *refresh_token* (logout).

        Marks the corresponding token entry as revoked in the database so it
        can no longer be used to obtain new access tokens.
        """
        try:
            payload = self.__jwt_utils.decode_token(refresh_token)
        except Exception:  # noqa: BLE001
            self.__audit.warning("logout_invalid_token")
            return

        jti = payload.get("jti")
        if not jti:
            return

        token = await self.__refresh_token_repo.get_by_jti_hash(
            sha256(jti.encode()).hexdigest()
        )
        if token:
            token.revoked = True
            await self.__refresh_token_repo.save(token)
            self.__audit.info("user_logout_success", user_id=payload.get("sub"))
        else:
            self.__audit.warning("logout_token_not_found", jti=jti)
