"""Unit tests for utils.jwt_keys.format_public_key_to_jwk"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import settings
from app.schemas.jwks import JWK
from app.utils import jwt as jwt_utils
from app.utils.jwt_keys import format_public_key_to_jwk, get_verifying_keys
from app.utils.jwt_rotation import Key

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def _b64url_uint(integer: int) -> str:
    byte_length = (integer.bit_length() + 7) // 8
    as_bytes = integer.to_bytes(byte_length, "big")
    return base64.urlsafe_b64encode(as_bytes).rstrip(b"=").decode("ascii")


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


def test_format_public_key_to_jwk(monkeypatch: MonkeyPatch):
    """Verify that a PEM-encoded public key is correctly formatted as a JWK."""
    # This function is specifically for RSA keys, so ensure the environment reflects this.
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "RS256")

    pem_key = _generate_rsa_pem()
    kid = "test-kid-123"

    jwk_dict = format_public_key_to_jwk(pem_key, kid)

    assert jwk_dict["kid"] == kid
    assert jwk_dict["kty"] == "RSA"
    assert jwk_dict["use"] == "sig"
    assert jwk_dict["alg"] == settings.JWT_ALGORITHM
    assert "n" in jwk_dict
    assert "e" in jwk_dict


def test_get_verifying_keys(monkeypatch: MonkeyPatch):
    """
    Verify that get_verifying_keys returns only keys that have not been retired.
    """
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    # 1. Define a set of test keys
    active_pem = _generate_rsa_pem()
    retired_pem = _generate_rsa_pem()
    future_pem = _generate_rsa_pem()

    # 2. Mock the settings and runtime state
    monkeypatch.setattr(
        settings,
        "JWT_KEYS",
        {
            "active-key": active_pem,
            "retired-key": retired_pem,
            "future-key": future_pem,
        },
    )
    # This key was retired an hour ago, it should NOT be returned
    monkeypatch.setattr(jwt_utils, "_RETIRED_KEYS", {"retired-key": one_hour_ago})

    # 3. Call the function under test
    verifying_keys = get_verifying_keys()

    # 4. Assert the results
    assert len(verifying_keys) == 2
    kids = {key.kid for key in verifying_keys}
    assert "active-key" in kids
    assert "future-key" in kids
    assert "retired-key" not in kids

    # Verify the objects are of the correct type
    for key in verifying_keys:
        assert isinstance(key, Key)


# Helper to generate a dummy RSA key for testing
def _generate_rsa_pem() -> str:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem.decode("utf-8")
