from __future__ import annotations

"""Utility helpers for password hashing, verification and strength validation.

Centralised here so that domain/application layers can depend on these helpers
without importing FastAPI or other framework-specific code.
"""

import re

from passlib.context import CryptContext

# Passlib context for bcrypt hashing
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password must be at least 8 characters, contain at least one digit and one symbol
_PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*()_+=\-]).{8,100}$")


def get_password_hash(password: str) -> str:  # pragma: no cover — thin wrapper
    """Hash a plaintext password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(
    plain_password: str, hashed_password: str
) -> bool:  # pragma: no cover
    """Verify a plaintext password against a given bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> bool:
    """Return True if *password* satisfies the project strength policy."""
    return bool(_PASSWORD_REGEX.match(password))
