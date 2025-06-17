from __future__ import annotations

"""JWT utility helpers leveraging python-jose.

NOTE: Functions raise NotImplementedError until Subtask 4.7 implementation
is completed. Unit tests for TDD will initially fail against these stubs.
"""

import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


class JWTUtils:
    """Helper class encapsulating JWT creation and decoding logic."""

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_sign_key() -> str | bytes:  # pragma: no cover
        """Return the key used to sign tokens based on algorithm."""
        alg = settings.JWT_ALGORITHM
        if alg.startswith("HS"):
            if not settings.JWT_SECRET_KEY:
                raise RuntimeError("JWT_SECRET_KEY must be set for HS* algorithms")
            return settings.JWT_SECRET_KEY
        if alg.startswith("RS"):
            if not settings.JWT_PRIVATE_KEY_PATH:
                raise RuntimeError(
                    "JWT_PRIVATE_KEY_PATH must be set for RS* algorithms"
                )
            return JWTUtils._load_key(settings.JWT_PRIVATE_KEY_PATH)
        raise RuntimeError(f"Unsupported JWT_ALGORITHM: {alg}")

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_verify_key() -> str | bytes:  # pragma: no cover
        """Return the key used to verify tokens based on algorithm."""
        alg = settings.JWT_ALGORITHM
        if alg.startswith("HS"):
            # Symmetric key – same as sign key
            return JWTUtils._get_sign_key()
        if alg.startswith("RS"):
            if not settings.JWT_PUBLIC_KEY_PATH:
                raise RuntimeError("JWT_PUBLIC_KEY_PATH must be set for RS* algorithms")
            return JWTUtils._load_key(settings.JWT_PUBLIC_KEY_PATH)
        raise RuntimeError(f"Unsupported JWT_ALGORITHM: {alg}")

    @staticmethod
    def _load_key(path: str) -> str:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    @staticmethod
    def create_access_token(
        subject: str | int,
        *,
        expires_delta: timedelta | None = None,
        additional_claims: Dict[str, Any] | None = None,
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        payload: Dict[str, Any] = {
            "sub": str(subject),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": uuid.uuid4().hex,
        }
        if additional_claims:
            payload.update(additional_claims)
        token = jwt.encode(
            payload,
            JWTUtils._get_sign_key(),
            algorithm=settings.JWT_ALGORITHM,
        )
        return token

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                JWTUtils._get_verify_key(),
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except ExpiredSignatureError as exc:
            raise exc
        except JWTError as exc:
            raise exc
