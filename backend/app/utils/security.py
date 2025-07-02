from __future__ import annotations

"""Utility helpers for password hashing, verification and strength validation.

Centralised here so that domain/application layers can depend on these helpers
without importing FastAPI or other framework-specific code.
"""

import re

from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password Hasher Utility
# ---------------------------------------------------------------------------


class PasswordHasher:  # noqa: D101 – simple utility wrapper
    """Utility class for hashing & verifying passwords.

    Uses *passlib*'s :class:`~passlib.context.CryptContext` under the hood and
    retrieves the bcrypt cost factor from :data:`settings.BCRYPT_ROUNDS` so it
    can be tuned per-environment (e.g. lower in CI).
    """

    _context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=settings.BCRYPT_ROUNDS,
    )

    @classmethod
    def hash_password(cls, plain: str) -> str:  # pragma: no cover – thin wrapper
        """Return a bcrypt hash for *plain* password."""

        return cls._context.hash(plain)

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:  # pragma: no cover
        """Verify *plain* password against *hashed* digest."""

        return cls._context.verify(plain, hashed)

    @classmethod
    def needs_update(cls, hashed: str) -> bool:  # pragma: no cover
        """Return *True* if *hashed* should be re-hashed with stronger params."""

        return cls._context.needs_update(hashed)


# ---------------------------------------------------------------------------
# Password strength validation helpers (unchanged)
# ---------------------------------------------------------------------------

_PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,100}$")


def get_password_hash(password: str) -> str:  # pragma: no cover — legacy alias
    """Legacy helper – delegates to :pyclass:`PasswordHasher`."""

    return PasswordHasher.hash_password(password)


def verify_password(
    plain_password: str, hashed_password: str
) -> bool:  # pragma: no cover – legacy alias
    """Legacy helper delegating to :pyclass:`PasswordHasher`."""

    return PasswordHasher.verify_password(plain_password, hashed_password)


def validate_password_strength(password: str) -> bool:
    """Return True if *password* satisfies the project strength policy."""
    return bool(_PASSWORD_REGEX.match(password))
