from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone


def generate_token(expiration_minutes: int = 30) -> tuple[str, str, datetime]:
    """Return (token, token_hash, expires_at)."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
    return token, token_hash, expires_at


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_verification_token(
    expiration_minutes: int = 60 * 24,
) -> tuple[str, str, datetime]:
    """Generate token tuple for email verification."""
    return generate_token(expiration_minutes)
