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

        from app.domain.errors import (  # local import to avoid circular deps
            InactiveUserError,
            InvalidCredentialsError,
        )

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

            security.PasswordHasher.verify_password(password, _dummy_hash())
            raise InvalidCredentialsError()

        # Optional inactive flag check if column exists
        if getattr(user, "is_active", True) is False:
            raise InactiveUserError()

        if not security.PasswordHasher.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        # Issue tokens
        access_token = JWTUtils.create_access_token(str(user.id))
        refresh_token = JWTUtils.create_refresh_token(str(user.id))

        # Persist refresh token JTI hash
        from jose import jwt as jose_jwt  # local import to defer heavy dep

        payload = jose_jwt.get_unverified_claims(refresh_token)
        jti = payload["jti"]
        ttl = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        rt_repo = RefreshTokenRepository(self._repo._session)
        await rt_repo.create_from_jti(jti, user.id, ttl)

        audit("user_login_success", user_id=str(user.id), jti=jti)
        _LOGGER.info("user_login_success", extra={"user_id": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
