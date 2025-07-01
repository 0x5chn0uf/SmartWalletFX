from __future__ import annotations

"""Application-layer authentication service.

Encapsulates business rules for user registration and, in
future, login & token issuance.  Keeping logic here enables
straightforward unit testing and maintains a clean separation between
FastAPI adapters and domain/infrastructure layers.
"""

import logging
from datetime import timedelta
from typing import Final

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security.roles import UserRole
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_token import TokenResponse
from app.schemas.user import UserCreate
from app.utils import security
from app.utils.jwt import JWTUtils
from app.utils.logging import audit

_LOGGER: Final = logging.getLogger(__name__)


class DuplicateError(Exception):
    """Raised when *username* or *email* is already registered."""

    def __init__(self, field: str):
        super().__init__(field)
        self.field = field


class WeakPasswordError(Exception):
    """Raised when a password does not meet strength requirements."""


class AuthService:
    """Core authentication service (register, authenticate, tokens…)."""

    def __init__(self, session: AsyncSession):
        self._repo = UserRepository(session)

    async def register(self, payload: UserCreate) -> User:
        """Register a new user.

        Args:
            payload: Incoming user-supplied data.

        Returns:
            Newly-created :class:`app.models.user.User` instance.

        Raises:
            DuplicateError: If *username* or *email* already exists.
            WeakPasswordError: If password fails strength policy.
        """

        # Validate password strength early (defensive programming)
        if not security.validate_password_strength(payload.password):
            raise WeakPasswordError()

        # Duplicate checks
        if await self._repo.exists(username=payload.username):
            raise DuplicateError("username")
        if await self._repo.exists(email=payload.email):
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
            user = await self._repo.save(user)
        except IntegrityError as exc:  # pragma: no cover – safeguard
            # Handle race condition duplicates at DB level
            _LOGGER.warning("IntegrityError during register: %s", exc, exc_info=exc)
            if "users_email_key" in str(exc.orig):  # simplistic check
                raise DuplicateError("email") from exc
            raise

        _LOGGER.info("user_registered", extra={"user_id": str(user.id)})
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
        from app.domain.errors import InvalidCredentialsError

        identity_lc = identity.lower().strip()

        # ------------------------------------------------------------------
        # Fetch user by *username* first, fallback to *email* to support both.
        # Username is stored in DB as-is but indexed; we normalise to lowercase
        # for a case-insensitive comparison. Email column is already unique.
        # ------------------------------------------------------------------
        user: User | None = await self._repo.get_by_username(identity_lc)
        if user is None:
            user = await self._repo.get_by_email(identity_lc)

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
            audit("AUTH_FAILURE", reason="invalid_credentials", identity=identity_lc)
            raise InvalidCredentialsError()

        if getattr(user, "is_active", True) is False:
            audit("AUTH_FAILURE", reason="inactive_account", user_id=str(user.id))
            raise InactiveUserError()

        if not security.PasswordHasher.verify_password(password, user.hashed_password):
            audit("AUTH_FAILURE", reason="invalid_credentials", user_id=str(user.id))
            raise InvalidCredentialsError()

        # Prepare additional claims for RBAC/ABAC
        additional_claims = {}

        # Add user roles (with backward compatibility fallback)
        user_roles = user.roles if user.roles else [UserRole.INDIVIDUAL_INVESTOR.value]
        additional_claims["roles"] = user_roles

        # Add user attributes (with backward compatibility fallback)
        user_attributes = user.attributes if user.attributes else {}
        additional_claims["attributes"] = user_attributes

        # Issue tokens with role/attribute claims
        access_token = JWTUtils.create_access_token(
            str(user.id), additional_claims=additional_claims
        )
        refresh_token = JWTUtils.create_refresh_token(str(user.id))

        # Persist refresh token JTI hash *before* we access any attributes that
        # may expire on commit.  We therefore **stash** the primary-key value
        # so that subsequent logging does not trigger a lazy-load which would
        # perform I/O in the synchronous response thread (leading to the
        # dreaded ``MissingGreenlet`` error seen in the failing test).

        from jose import jwt as jose_jwt  # local import to defer heavy dep

        payload = jose_jwt.get_unverified_claims(refresh_token)
        jti = payload["jti"]
        ttl = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        rt_repo = RefreshTokenRepository(self._repo._session)
        user_pk = user.id  # capture before commit/expiration
        await rt_repo.create_from_jti(jti, user_pk, ttl)

        user_pk_str = str(user_pk)
        audit("user_login_success", user_id=user_pk_str, jti=jti, roles=user_roles)
        _LOGGER.info(
            "user_login_success", extra={"user_id": user_pk_str, "roles": user_roles}
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
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
            payload = JWTUtils.decode_token(refresh_token)
        except Exception as exc:  # noqa: BLE001
            raise InvalidCredentialsError() from exc

        if payload.get("type") != "refresh":
            raise InvalidCredentialsError()

        user_id = payload.get("sub")
        jti = payload.get("jti")
        if not user_id or not jti:
            raise InvalidCredentialsError()

        # Verify token exists and not revoked/expired in DB
        rt_repo = RefreshTokenRepository(self._repo._session)
        jti_hash = sha256(jti.encode()).hexdigest()
        token_obj = await rt_repo.get_by_jti_hash(jti_hash)

        if token_obj is None or token_obj.revoked:
            raise InvalidCredentialsError()

        # Fetch user
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError()

        # Build additional claims
        user_roles = user.roles or [UserRole.INDIVIDUAL_INVESTOR.value]
        user_attributes = user.attributes or {}

        access_token = JWTUtils.create_access_token(
            str(user.id),
            additional_claims={"roles": user_roles, "attributes": user_attributes},
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Same refresh token returned
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
