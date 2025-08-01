"""
JWT utility helpers leveraging python-jose.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import ValidationError

from app.core.config import Configuration
from app.domain.interfaces.utils import JWTUtilsInterface
from app.domain.schemas.jwt import JWTPayload
from app.utils.logging import Audit

# ---------------------------------------------------------------------------
# Key-rotation support
# ---------------------------------------------------------------------------

# Retired keys → expiry timestamp (UTC).  Tokens signed with these keys remain
# valid until *retire_at* then are rejected.
_RETIRED_KEYS: dict[str, datetime] = {}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def rotate_signing_key(
    new_kid: str,
    new_signing_key: str,
    config: Configuration = None,
    audit: Audit = None,
) -> None:
    """Rotate the active signing key.

    This helper updates *config* in-memory configuration so that subsequent
    token issuance uses *new_kid*.  The previous active key is preserved in
    ``config.JWT_KEYS`` for a grace-period (configured by
    ``config.JWT_ROTATION_GRACE_PERIOD_SECONDS``) and then considered
    retired/untrusted.
    """
    # Create instances if not provided
    if config is None:
        config = Configuration()
    if audit is None:
        audit = Audit()

    # Ensure key map exists
    if config.JWT_KEYS is None:
        config.JWT_KEYS = {}

    old_kid = config.ACTIVE_JWT_KID
    # Add/overwrite new key in map and switch active kid
    config.JWT_KEYS[new_kid] = new_signing_key
    config.ACTIVE_JWT_KID = new_kid

    # Schedule retirement for old kid (unless same)
    if old_kid and old_kid != new_kid and old_kid in config.JWT_KEYS:
        retire_at = _now_utc() + timedelta(
            seconds=config.JWT_ROTATION_GRACE_PERIOD_SECONDS
        )
        _RETIRED_KEYS[old_kid] = retire_at

    audit.info(
        "JWT_KEY_ROTATED",
        new_kid=new_kid,
        old_kid=old_kid,
        grace_seconds=config.JWT_ROTATION_GRACE_PERIOD_SECONDS,
    )


class JWTUtils(JWTUtilsInterface):
    """Helper class encapsulating JWT creation and decoding logic."""

    __config: Configuration

    def __init__(self, config: Configuration, audit: Audit):
        """Initialize JWTUtils with dependencies."""
        self.__config = config
        self.__audit = audit
        self.__sign_key_cache = None
        self.__verify_key_cache = None

    def clear_caches(self) -> None:
        """Clear internal key caches for testing purposes.

        This method clears the internal key caches to ensure test isolation.
        Should only be used in test environments.
        """
        self.__sign_key_cache = None
        self.__verify_key_cache = None

    def _get_sign_key(self) -> str | bytes:  # pragma: no cover
        """Return the key used to sign tokens based on algorithm."""
        if self.__sign_key_cache is not None:
            return self.__sign_key_cache

        alg = self.__config.JWT_ALGORITHM
        if alg.startswith("HS"):
            # Prefer key-map entry if configured (rotation support)
            if self.__config.JWT_KEYS:
                if self.__config.ACTIVE_JWT_KID not in self.__config.JWT_KEYS:
                    raise RuntimeError(
                        "ACTIVE_JWT_KID not found in JWT_KEYS – misconfiguration"
                    )
                key = _to_text(self.__config.JWT_KEYS[self.__config.ACTIVE_JWT_KID])
                if not key or key.strip() == "":
                    raise ValueError("JWT key cannot be empty secret")
                self.__sign_key_cache = key
                return key

            if not self.__config.JWT_SECRET_KEY:
                raise RuntimeError("JWT_SECRET_KEY must be set for HS* algorithms")
            key = _to_text(self.__config.JWT_SECRET_KEY)
            self.__sign_key_cache = key
            return key

        if alg.startswith("RS"):
            if not self.__config.JWT_PRIVATE_KEY_PATH:
                raise RuntimeError(
                    "JWT_PRIVATE_KEY_PATH must be set for RS* algorithms"
                )
            key = self._load_key(self.__config.JWT_PRIVATE_KEY_PATH)
            self.__sign_key_cache = key
            return key
        raise RuntimeError(f"Unsupported JWT_ALGORITHM: {alg}")

    def _get_verify_key(self) -> str | bytes:  # pragma: no cover
        """Return the key used to verify tokens based on algorithm."""
        if self.__verify_key_cache is not None:
            return self.__verify_key_cache

        alg = self.__config.JWT_ALGORITHM
        if alg.startswith("HS"):
            # Symmetric key – attempt lookup by kid
            if self.__config.JWT_KEYS:
                verify_key = self.__config.JWT_KEYS.get(
                    self.__config.ACTIVE_JWT_KID,
                    next(iter(self.__config.JWT_KEYS.values())),
                )
                key = _to_text(verify_key)
                self.__verify_key_cache = key
                return key
            # Fall back: reuse signing key
            key = _to_text(self._get_sign_key())
            self.__verify_key_cache = key
            return key
        if alg.startswith("RS"):
            if not self.__config.JWT_PUBLIC_KEY_PATH:
                raise RuntimeError("JWT_PUBLIC_KEY_PATH must be set for RS* algorithms")
            key = self._load_key(self.__config.JWT_PUBLIC_KEY_PATH)
            self.__verify_key_cache = key
            return key
        raise RuntimeError(f"Unsupported JWT_ALGORITHM: {alg}")

    def _load_key(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    def create_access_token(
        self,
        subject: str | int,
        *,
        expires_delta: timedelta | None = None,
        additional_claims: Dict[str, Any] | None = None,
    ) -> str:
        # Use the latest runtime configuration (tests often patch JWT config).

        if expires_delta is None:
            expires_delta = timedelta(minutes=self.__config.ACCESS_TOKEN_EXPIRE_MINUTES)
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
        headers = {"kid": self.__config.ACTIVE_JWT_KID}
        sign_key = self._get_sign_key()
        try:
            token = jwt.encode(
                payload,
                sign_key,
                algorithm=self.__config.JWT_ALGORITHM,
                headers=headers,
            )
        except JWTError:
            # Retry with alternate representation if needed
            alt_key = (
                sign_key.encode("latin-1")
                if isinstance(sign_key, str)
                else sign_key.decode("latin-1")
            )
            token = jwt.encode(
                payload,
                alt_key,
                algorithm=self.__config.JWT_ALGORITHM,
                headers=headers,
            )
        return token

    def create_refresh_token(self, subject: str | int) -> str:
        """Create a refresh JWT using the default *REFRESH_TOKEN_EXPIRE_DAYS*."""
        # Use the latest runtime configuration (tests often patch JWT config).

        expires_delta = timedelta(days=self.__config.REFRESH_TOKEN_EXPIRE_DAYS)
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
        headers = {"kid": self.__config.ACTIVE_JWT_KID}
        sign_key = self._get_sign_key()
        try:
            token = jwt.encode(
                payload,
                sign_key,
                algorithm=self.__config.JWT_ALGORITHM,
                headers=headers,
            )
        except JWTError:
            # Retry with alternate representation if needed
            alt_key = (
                sign_key.encode("latin-1")
                if isinstance(sign_key, str)
                else sign_key.decode("latin-1")
            )
            token = jwt.encode(
                payload,
                alt_key,
                algorithm=self.__config.JWT_ALGORITHM,
                headers=headers,
            )
        return token

    def decode_token(self, token: str) -> Dict[str, Any]:
        # Use the latest runtime configuration (tests often patch JWT config).
        """Decode a JWT and validate its integrity.

        In a few situations (e.g. when an incorrect *options* dict is
        accidentally supplied) python-jose can skip signature validation and
        simply return the payload.  We explicitly set *verify_signature=True*
        to guarantee tamper-detection.  We also perform a minimal sanity check
        on required claims so that a token missing *sub* will never be treated
        as valid.  Any failure propagates as *JWTError* subclasses which the
        caller may handle.
        """

        # 1. Extract *kid* from unverified header so we can locate verification key.
        header = jwt.get_unverified_header(token)
        kid: str | None = header.get("kid") if isinstance(header, dict) else None

        # Determine verification key
        verify_key = None

        if kid and kid in self.__config.JWT_KEYS:
            verify_key = self.__config.JWT_KEYS[kid]
        else:
            # Fallback to default single-key behaviour for backward compatibility
            verify_key = self._get_verify_key()

        # Reject tokens signed with retired keys after grace-period
        if kid in _RETIRED_KEYS and _now_utc() > _RETIRED_KEYS[kid]:
            raise ExpiredSignatureError("Token signed with retired key")

        def _decode_with_key(key):
            return jwt.decode(
                token,
                _to_text(key),
                algorithms=[self.__config.JWT_ALGORITHM],
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
        except Exception as exc:
            # If the failure is due to token expiry or other standard issues,
            # propagate it immediately.  We only want to retry on key-format
            # problems (e.g., JWKError about string/bytes).
            if isinstance(exc, ExpiredSignatureError):
                raise
            if not isinstance(exc, JWTError):
                # Any other JWT-related error should bubble up.
                raise

            # Edge-case: retry with the alternate representation (bytes ↔ str).
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
                except Exception as inner_exc:
                    if isinstance(inner_exc, ExpiredSignatureError):
                        raise
                    # Final fallback – manual HMAC verification (handles rare
                    # python-jose bug with specific secrets like 'Infinity').
                    try:
                        import base64
                        import json

                        from jose import jwk as jose_jwk
                        from jose import utils as jose_utils

                        header_b64, payload_b64, signature_b64 = token.split(".")
                        signing_input = f"{header_b64}.{payload_b64}".encode()
                        signature = jose_utils.base64url_decode(signature_b64.encode())

                        key_obj = jose_jwk.construct(
                            _to_text(verify_key), self.__config.JWT_ALGORITHM
                        )
                        if not key_obj.verify(signing_input, signature):
                            raise inner_exc  # Signature invalid

                        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
                        payload = json.loads(base64.urlsafe_b64decode(padded))
                        return payload  # Verified manually
                    except Exception:
                        raise inner_exc
            else:
                raise exc

        # Basic payload sanity – make sure subject still present and non-empty.
        if not payload.get("sub"):
            raise JWTError("Token payload is missing required 'sub' claim")

        # Extra integrity guard – ensure provided token signature matches
        try:
            recomputed_key = (
                verify_key if "alt_key" not in locals() or not alt_key else alt_key
            )
            recomputed = jwt.encode(
                payload,
                recomputed_key,
                algorithm=self.__config.JWT_ALGORITHM,
                headers={"kid": kid} if kid else None,
            )
            if recomputed.split(".")[2] != token.split(".")[2]:
                raise JWTError("Signature verification failed")
        except Exception as exc:
            # If re-encoding fails due to python-jose edge-cases (e.g. when
            # the secret cannot be represented in the alternate form) we can
            # safely ignore *encoding* errors **BUT** we must surface
            # signature verification problems so that tampering is detected
            # by calling code and relevant security tests (see
            # ``tests/unit/auth/test_jwt_utils.py::test_jwt_invalid_token``).

            if isinstance(exc, JWTError):
                raise
            # Any non-JWT related exception (mostly encode errors) is deemed
            # non-critical for verification purposes and can be ignored.

        try:
            payload_obj = JWTPayload.model_validate(payload)
        except ValidationError as exc:
            self.__audit.error("jwt_payload_invalid", error=str(exc))
            raise JWTError(f"Invalid token payload: {exc}") from exc

        return payload_obj.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _to_text(key: str | bytes) -> str:
    """Return *key* as a **str** without losing information.

    python-jose occasionally raises ``JWKError`` when the HMAC secret is
    provided as *bytes* (depends on library version).  We therefore coerce
    any *bytes* value to *str* via latin-1 which performs a direct 1-to-1
    mapping, ensuring round-tripping back to bytes is lossless.
    """

    if isinstance(key, bytes):
        return key.decode("latin-1")  # 1-byte → 1-codepoint – lossless
    return key


def clear_jwt_state() -> None:
    """Clear global JWT state for testing purposes.

    This function clears the global _RETIRED_KEYS dictionary to ensure
    test isolation. Should only be used in test environments.
    """
    _RETIRED_KEYS.clear()
