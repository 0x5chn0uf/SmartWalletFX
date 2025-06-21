"""Utility helpers for converting public keys to JSON Web Keys (JWK).

This module currently supports RSA public keys which are the only key type
used by our JWT authentication system (RS256).  Support for additional key
types (EC, OKP, symmetric) can be added in future tasks.
"""

from __future__ import annotations

import base64
from typing import Any, Dict

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.schemas.jwks import JWK

__all__ = ["format_public_key_to_jwk"]


def _b64url_uint(integer: int) -> str:
    """Encode an unsigned integer as base64url without padding."""

    byte_length = (integer.bit_length() + 7) // 8
    as_bytes = integer.to_bytes(byte_length, "big")
    return base64.urlsafe_b64encode(as_bytes).rstrip(b"=").decode("ascii")


def format_public_key_to_jwk(
    public_key_pem: str | bytes, kid: str, *, alg: str = "RS256"
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
        :class:`app.schemas.jwks.JWK`.
    """

    if isinstance(public_key_pem, str):
        key_bytes = public_key_pem.encode()
    else:
        key_bytes = public_key_pem

    public_key = serialization.load_pem_public_key(key_bytes, backend=default_backend())

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
