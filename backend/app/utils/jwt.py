"""JWT utility helpers leveraging python-jose."""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict

from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.schemas.jwt import JWTPayload
from app.utils.logging import Audit


class JWTService:
    """Encapsulate JWT creation and verification logic."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._retired_keys: dict[str, datetime] = {}

    # ------------------------------------------------------------------
    # Key rotation
    # ------------------------------------------------------------------
    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    def rotate_signing_key(self, new_kid: str, new_signing_key: str) -> None:
        """Rotate active signing key and schedule retirement of the old one."""

        if self._settings.JWT_KEYS is None:
            self._settings.JWT_KEYS = {}

        old_kid = self._settings.ACTIVE_JWT_KID
        self._settings.JWT_KEYS[new_kid] = new_signing_key
        self._settings.ACTIVE_JWT_KID = new_kid

        if old_kid and old_kid != new_kid and old_kid in self._settings.JWT_KEYS:
            retire_at = self._now_utc() + timedelta(
                seconds=self._settings.JWT_ROTATION_GRACE_PERIOD_SECONDS
            )
            with self._lock:
                self._retired_keys[old_kid] = retire_at

        Audit.info(
            "JWT_KEY_ROTATED",
            new_kid=new_kid,
            old_kid=old_kid,
            grace_seconds=self._settings.JWT_ROTATION_GRACE_PERIOD_SECONDS,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @lru_cache(maxsize=1)
    def _get_sign_key(self) -> str | bytes:  # pragma: no cover
        alg = self._settings.JWT_ALGORITHM
        if alg.startswith("HS"):
            if self._settings.JWT_KEYS:
                if self._settings.ACTIVE_JWT_KID not in self._settings.JWT_KEYS:
                    raise RuntimeError(
                        "ACTIVE_JWT_KID not found in JWT_KEYS – misconfiguration"
                    )
                return _to_text(self._settings.JWT_KEYS[self._settings.ACTIVE_JWT_KID])
            if not self._settings.JWT_SECRET_KEY:
                raise RuntimeError("JWT_SECRET_KEY must be set for HS* algorithms")
            return _to_text(self._settings.JWT_SECRET_KEY)

        if alg.startswith("RS"):
            if not self._settings.JWT_PRIVATE_KEY_PATH:
                raise RuntimeError(
                    "JWT_PRIVATE_KEY_PATH must be set for RS* algorithms"
                )
            return self._load_key(self._settings.JWT_PRIVATE_KEY_PATH)
        raise RuntimeError(f"Unsupported JWT_ALGORITHM: {alg}")

    @lru_cache(maxsize=1)
    def _get_verify_key(self) -> str | bytes:  # pragma: no cover
        alg = self._settings.JWT_ALGORITHM
        if alg.startswith("HS"):
            if self._settings.JWT_KEYS:
                verify_key = self._settings.JWT_KEYS.get(
                    self._settings.ACTIVE_JWT_KID,
                    next(iter(self._settings.JWT_KEYS.values())),
                )
                return _to_text(verify_key)
            return _to_text(self._get_sign_key())
        if alg.startswith("RS"):
            if not self._settings.JWT_PUBLIC_KEY_PATH:
                raise RuntimeError("JWT_PUBLIC_KEY_PATH must be set for RS* algorithms")
            return self._load_key(self._settings.JWT_PUBLIC_KEY_PATH)
        raise RuntimeError(f"Unsupported JWT_ALGORITHM: {alg}")

    @staticmethod
    def _load_key(path: str) -> str:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_access_token(
        self,
        subject: str | int,
        *,
        expires_delta: timedelta | None = None,
        additional_claims: Dict[str, Any] | None = None,
    ) -> str:
        self._get_sign_key.cache_clear()
        self._get_verify_key.cache_clear()

        if expires_delta is None:
            expires_delta = timedelta(
                minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        payload: Dict[str, Any] = {
            "sub": str(subject),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": uuid.uuid4().hex,
            "type": "access",
        }
        if additional_claims:
            payload.update(additional_claims)
        headers = {"kid": self._settings.ACTIVE_JWT_KID}
        sign_key = self._get_sign_key()
        try:
            token = jwt.encode(
                payload,
                sign_key,
                algorithm=self._settings.JWT_ALGORITHM,
                headers=headers,
            )
        except JWTError:
            alt_key = (
                sign_key.encode("latin-1")
                if isinstance(sign_key, str)
                else sign_key.decode("latin-1")
            )
            token = jwt.encode(
                payload,
                alt_key,
                algorithm=self._settings.JWT_ALGORITHM,
                headers=headers,
            )
        return token

    def create_refresh_token(self, subject: str | int) -> str:
        self._get_sign_key.cache_clear()
        self._get_verify_key.cache_clear()

        expires_delta = timedelta(days=self._settings.REFRESH_TOKEN_EXPIRE_DAYS)
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        jti = uuid.uuid4().hex
        payload: Dict[str, Any] = {
            "sub": str(subject),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": jti,
            "type": "refresh",
        }
        token = jwt.encode(
            payload,
            self._get_sign_key(),
            algorithm=self._settings.JWT_ALGORITHM,
        )
        return token

    def decode_token(self, token: str) -> Dict[str, Any]:
        self._get_sign_key.cache_clear()
        self._get_verify_key.cache_clear()

        header = jwt.get_unverified_header(token)
        kid: str | None = header.get("kid") if isinstance(header, dict) else None

        verify_key = None
        if kid and kid in self._settings.JWT_KEYS:
            verify_key = self._settings.JWT_KEYS[kid]
        else:
            verify_key = self._get_verify_key()

        if kid in self._retired_keys and self._now_utc() > self._retired_keys[kid]:
            raise ExpiredSignatureError("Token signed with retired key")

        def _decode_with_key(key: str | bytes):
            return jwt.decode(
                token,
                _to_text(key),
                algorithms=[self._settings.JWT_ALGORITHM],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                    "require": ["sub", "jti", "exp"],
                },
            )

        try:
            payload = _decode_with_key(verify_key)
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, ExpiredSignatureError):
                raise
            if not isinstance(exc, JWTError):
                raise

            alt_key = None
            if isinstance(verify_key, bytes):
                try:
                    alt_key = verify_key.decode("latin-1")
                except Exception:
                    alt_key = None
            elif isinstance(verify_key, str):
                alt_key = verify_key.encode("latin-1")

            if alt_key is not None:
                try:
                    payload = _decode_with_key(alt_key)
                except Exception as inner_exc:  # noqa: BLE001
                    if isinstance(inner_exc, ExpiredSignatureError):
                        raise
                    try:
                        import base64
                        import json

                        from jose import jwk as jose_jwk
                        from jose import utils as jose_utils

                        header_b64, payload_b64, signature_b64 = token.split(".")
                        signing_input = f"{header_b64}.{payload_b64}".encode()
                        signature = jose_utils.base64url_decode(signature_b64.encode())
                        key_obj = jose_jwk.construct(
                            _to_text(verify_key), self._settings.JWT_ALGORITHM
                        )
                        if not key_obj.verify(signing_input, signature):
                            raise inner_exc
                        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
                        payload = json.loads(base64.urlsafe_b64decode(padded))
                        return payload
                    except Exception:
                        raise inner_exc
            else:
                raise exc

        if not payload.get("sub"):
            raise JWTError("Token payload is missing required 'sub' claim")

        try:
            recomputed_key = (
                verify_key if "alt_key" not in locals() or not alt_key else alt_key
            )
            recomputed = jwt.encode(
                payload,
                recomputed_key,
                algorithm=self._settings.JWT_ALGORITHM,
                headers={"kid": kid} if kid else None,
            )
            if recomputed.split(".")[2] != token.split(".")[2]:
                raise JWTError("Signature verification failed")
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, JWTError):
                raise

        try:
            payload_obj = JWTPayload.model_validate(payload)
        except ValidationError as exc:
            Audit.error("jwt_payload_invalid", error=str(exc))
            raise JWTError(f"Invalid token payload: {exc}") from exc

        return payload_obj.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Module-level helpers for backward compatibility
# ---------------------------------------------------------------------------

jwt_service = JWTService(settings)
_RETIRED_KEYS = jwt_service._retired_keys


def rotate_signing_key(new_kid: str, new_signing_key: str) -> None:
    jwt_service._settings = settings
    jwt_service.rotate_signing_key(new_kid, new_signing_key)


_now_utc = JWTService._now_utc


@lru_cache(maxsize=1)
def _jwtutils_get_sign_key() -> str | bytes:
    jwt_service._settings = settings
    jwt_service._get_sign_key.cache_clear()
    return jwt_service._get_sign_key()


@lru_cache(maxsize=1)
def _jwtutils_get_verify_key() -> str | bytes:
    jwt_service._settings = settings
    jwt_service._get_verify_key.cache_clear()
    return jwt_service._get_verify_key()


class JWTUtils:
    """Backward-compatible static wrapper around :class:`JWTService`."""

    @staticmethod
    def rotate_signing_key(new_kid: str, new_signing_key: str) -> None:
        jwt_service._settings = settings
        jwt_service.rotate_signing_key(new_kid, new_signing_key)

    @staticmethod
    def create_access_token(
        subject: str | int,
        *,
        expires_delta: timedelta | None = None,
        additional_claims: Dict[str, Any] | None = None,
    ) -> str:
        jwt_service._settings = settings
        return jwt_service.create_access_token(
            subject,
            expires_delta=expires_delta,
            additional_claims=additional_claims,
        )

    @staticmethod
    def create_refresh_token(subject: str | int) -> str:
        jwt_service._settings = settings
        return jwt_service.create_refresh_token(subject)

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        jwt_service._settings = settings
        return jwt_service.decode_token(token)

    _get_sign_key = staticmethod(_jwtutils_get_sign_key)

    _get_verify_key = staticmethod(_jwtutils_get_verify_key)

    _load_key = staticmethod(jwt_service._load_key)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _to_text(key: str | bytes) -> str:
    """Return *key* as ``str`` without losing information."""

    if isinstance(key, bytes):
        return key.decode("latin-1")
    return key
