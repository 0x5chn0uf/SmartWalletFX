from __future__ import annotations

"""Application-layer authentication service.

Encapsulates business rules for user registration and, in
future, login & token issuance.  Keeping logic here enables
straightforward unit testing and maintains a clean separation between
FastAPI adapters and domain/infrastructure layers.
"""

import logging
from typing import Final

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.utils import security

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

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

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
