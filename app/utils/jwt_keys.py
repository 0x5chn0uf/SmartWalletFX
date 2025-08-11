"""Utility helpers for converting public keys to JSON Web Keys (JWK).

This module currently supports RSA public keys which are the only key type
used by our JWT authentication system (RS256).  Support for additional key
types (EC, OKP, symmetric) can be added in future tasks.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any, Dict

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import Configuration
from app.domain.interfaces.utils import JWTKeyUtilsInterface
from app.domain.schemas.jwks import JWK
from app.utils.jwt_rotation import Key

__all__ = [
    "JWTKeyUtils",
    "_b64url_uint",
]


def _b64url_uint(integer: int) -> str:
    """Encode an unsigned integer as base64url without padding."""

    byte_length = (integer.bit_length() + 7) // 8
    as_bytes = integer.to_bytes(byte_length, "big")
    return base64.urlsafe_b64encode(as_bytes).rstrip(b"=").decode("ascii")


class JWTKeyUtils(JWTKeyUtilsInterface):
    """Utility class for JWT key operations."""

    def __init__(self, config: Configuration):
        """Initialize JWTKeyUtils with dependencies."""
        self.__config = config

    def get_signing_key(self) -> tuple[str, str]:
        """Get the active signing key and algorithm.

        Returns
        -------
        tuple[str, str]
            A tuple of (key, algorithm) where key is the PEM-encoded signing key
            and algorithm is the JWT algorithm (e.g., "HS256", "RS256").
        """
        active_kid = self.__config.ACTIVE_JWT_KID

        if active_kid not in self.__config.JWT_KEYS:
            raise ValueError(f"Active JWT key ID '{active_kid}' not found in JWT_KEYS")

        signing_key = self.__config.JWT_KEYS[active_kid]
        algorithm = self.__config.JWT_ALGORITHM

        return signing_key, algorithm

    def get_verifying_keys(self) -> list[Key]:
        """Return all keys that are currently valid for verifying signatures.

        This function builds a list of all known keys from
        ``Configuration.JWT_KEYS``,
        checks their retirement status against the runtime ``_RETIRED_KEYS`` map,
        and returns only those that are not yet expired.  This list is suitable
        for building a JWKS endpoint.

        Returns
        -------
        list[Key]
            A list of :class:`Key` objects representing non-retired public keys.
        """
        from app.utils import jwt as jwt_utils  # lazy import to avoid cycles

        now = datetime.now(timezone.utc)
        valid_keys: list[Key] = []

        for kid, pem_value in self.__config.JWT_KEYS.items():
            retired_at = jwt_utils._RETIRED_KEYS.get(
                kid
            )  # pylint: disable=protected-access

            # A key is considered valid for verification if its retirement time
            # has not yet passed.
            if retired_at and now >= retired_at:
                continue  # This key is retired, skip it.

            valid_keys.append(Key(kid=kid, value=pem_value, retired_at=retired_at))

        return valid_keys

    def format_public_key_to_jwk(
        self, public_key_pem: str | bytes, kid: str, *, alg: str = "RS256"
    ) -> Dict[str, Any]:
        """Convert an RSA public key to a JWK dictionary conforming to RFC-7517.

        Parameters
        ----------
        public_key_pem:
            The PEM encoded RSA public key as *str* or *bytes*.
        kid:
            Key identifier to place in the resulting JWK (must match JWT *kid* header).
        alg:
            Signature algorithm – defaults to "RS256".

        Returns
        -------
        Dict[str, Any]
            A dictionary representation of the key that validates against
            :class:`app.domain.schemas.jwks.JWK`.
        """
        if isinstance(public_key_pem, str):
            key_bytes = public_key_pem.encode()
        else:
            key_bytes = public_key_pem

        public_key = serialization.load_pem_public_key(
            key_bytes, backend=default_backend()
        )

        if not isinstance(public_key, rsa.RSAPublicKey):
            raise TypeError("Only RSA public keys are supported for JWKS export")

        numbers = public_key.public_numbers()
        n_b64 = _b64url_uint(numbers.n)
        e_b64 = _b64url_uint(numbers.e)

        jwk_dict: Dict[str, Any] = {
            "kty": "RSA",
            "use": "sig",
            "kid": kid,
            "alg": alg,
            "n": n_b64,
            "e": e_b64,
        }

        # Validate via Pydantic – raises if invalid and ensures types/values
        JWK(**jwk_dict)
        return jwk_dict
