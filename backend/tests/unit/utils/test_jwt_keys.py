"""Unit tests for utils.jwt_keys.format_public_key_to_jwk"""

from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.schemas.jwks import JWK
from app.utils.jwt_keys import format_public_key_to_jwk


def _b64url_uint(integer: int) -> str:
    byte_length = (integer.bit_length() + 7) // 8
    as_bytes = integer.to_bytes(byte_length, "big")
    return base64.urlsafe_b64encode(as_bytes).rstrip(b"=").decode("ascii")


@pytest.mark.unit
def test_format_public_key_to_jwk_roundtrip():
    """Ensure RSA public key is accurately converted to JWK fields n/e."""

    # Generate a temporary RSA key for testing (small key for speed)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = key.public_key()

    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    kid = "test-key-1"
    jwk_dict = format_public_key_to_jwk(pem, kid)

    # Validate via Pydantic (should raise if invalid)
    jwk_model = JWK(**jwk_dict)
    assert jwk_model.kid == kid
    assert jwk_model.kty == "RSA"
    assert jwk_model.use == "sig"
    assert jwk_model.alg == "RS256"

    # Cross-check n and e values
    numbers = public_key.public_numbers()
    assert jwk_dict["n"] == _b64url_uint(numbers.n)
    assert jwk_dict["e"] == _b64url_uint(numbers.e)
