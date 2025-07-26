"""Utility helpers for password hashing, verification and strength validation.

Centralised here so that domain/application layers can depend on these helpers
without importing FastAPI or other framework-specific code.
"""
from __future__ import annotations

import re

from passlib.context import CryptContext

from app.core.config import Configuration
from app.domain.interfaces.utils import PasswordHasherInterface

# ---------------------------------------------------------------------------
# Password Hasher Utility
# ---------------------------------------------------------------------------


class PasswordHasher(PasswordHasherInterface):  # noqa: D101 – simple utility wrapper
    """Utility class for hashing & verifying passwords.

    Uses *passlib*'s :class:`~passlib.context.CryptContext` under the hood and
    retrieves the bcrypt cost factor from :data:`config.BCRYPT_ROUNDS` so it
    can be tuned per-environment (e.g. lower in CI).
    """

    def __init__(self, config: Configuration):
        """Initialize PasswordHasher with dependencies."""
        self.__config = config
        self.__context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=config.BCRYPT_ROUNDS,
        )

    def hash_password(self, plain: str) -> str:  # pragma: no cover – thin wrapper
        """Return a bcrypt hash for *plain* password."""

        return self.__context.hash(plain)

    def verify_password(self, plain: str, hashed: str) -> bool:  # pragma: no cover
        """Verify *plain* password against *hashed* digest."""

        return self.__context.verify(plain, hashed)

    def needs_update(self, hashed: str) -> bool:  # pragma: no cover
        """Return *True* if *hashed* should be re-hashed with stronger params."""

        return self.__context.needs_update(hashed)


# ---------------------------------------------------------------------------
# Password strength validation helpers (unchanged)
# ---------------------------------------------------------------------------

_PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,100}$")

# Default instance for backward compatibility
_default_hasher = PasswordHasher(Configuration())


def get_password_hash(password: str) -> str:  # pragma: no cover — legacy alias
    """Legacy helper – delegates to :pyclass:`PasswordHasher`."""

    return _default_hasher.hash_password(password)


def verify_password(
    plain_password: str, hashed_password: str
) -> bool:  # pragma: no cover – legacy alias
    """Legacy helper delegating to :pyclass:`PasswordHasher`."""

    return _default_hasher.verify_password(plain_password, hashed_password)


def validate_password_strength(password: str) -> bool:
    """Return True if *password* satisfies the project strength policy."""
    return bool(_PASSWORD_REGEX.match(password))
