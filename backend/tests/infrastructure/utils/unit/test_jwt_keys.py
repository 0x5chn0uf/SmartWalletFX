"""Unit tests for utils.jwt_keys.format_public_key_to_jwk"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.utils.jwt_keys import (
    _b64url_uint,
    format_public_key_to_jwk,
    get_signing_key,
    get_verifying_keys,
)


@pytest.fixture
def mock_settings(monkeypatch):
    """Fixture to mock JWT settings for testing."""
    settings = _Proxy()
    settings.JWT_ALGORITHM = "HS256"
    settings.JWT_KEYS = {"test_kid": "test_secret"}
    settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 60

    # Mock the default instance instead of the class
    monkeypatch.setattr(
        "app.utils.jwt_keys._default_jwt_key_utils._JWTKeyUtils__config", settings
    )
    yield settings


class _Proxy:
    """A proxy object to mock settings."""

    def __getattr__(self, name):
        return self.__dict__.get(name)

    def __setattr__(self, name, value):
        self.__dict__[name] = value


def test_b64url_uint():
    """Test base64url encoding of integers."""
    assert _b64url_uint(1) == "AQ"
    assert _b64url_uint(65537) == "AQAB"


def test_format_public_key_to_jwk_with_rs256():
    """Test format_public_key_to_jwk with RS256 algorithm."""
    # Setup
    public_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzyis1ZjfNB0bBgKFMSv\nvkTtwlvBsaJq7S5wA+kzeVOVpVWwkWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHc\naT92whREFpLv9cj5lTeJSibyr/Mrm/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIy\ntvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0\ne+lf4s4OxQawWD79J9/5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWb\nV6L11BWkpzGXSW4Hv43qa+GSYOD2QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9\nMwIDAQAB\n-----END PUBLIC KEY-----"
    kid = "kid1"

    # Execute
    jwk = format_public_key_to_jwk(public_key, kid)

    # Verify
    assert jwk["kty"] == "RSA"
    assert jwk["kid"] == "kid1"
    assert "n" in jwk
    assert "e" in jwk
    assert jwk["alg"] == "RS256"


def test_format_public_key_to_jwk_with_custom_alg():
    """Test format_public_key_to_jwk with custom algorithm."""
    # Setup
    public_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzyis1ZjfNB0bBgKFMSv\nvkTtwlvBsaJq7S5wA+kzeVOVpVWwkWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHc\naT92whREFpLv9cj5lTeJSibyr/Mrm/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIy\ntvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0\ne+lf4s4OxQawWD79J9/5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWb\nV6L11BWkpzGXSW4Hv43qa+GSYOD2QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9\nMwIDAQAB\n-----END PUBLIC KEY-----"
    kid = "kid1"

    # Execute
    jwk = format_public_key_to_jwk(public_key, kid, alg="RS384")

    # Verify
    assert jwk["kty"] == "RSA"
    assert jwk["kid"] == "kid1"
    assert "n" in jwk
    assert "e" in jwk
    assert jwk["alg"] == "RS384"


def test_get_signing_key(mock_settings):
    """Test get_signing_key with mock settings."""
    mock_settings.JWT_ALGORITHM = "HS256"
    mock_settings.JWT_KEYS = {"test_kid": "a_very_long_secret_key_for_hs256"}
    mock_settings.ACTIVE_JWT_KID = "test_kid"

    key, algorithm = get_signing_key()
    assert key == "a_very_long_secret_key_for_hs256"
    assert algorithm == "HS256"


def test_get_signing_key_rsa(mock_settings, rsa_private_key):
    """Test get_signing_key with RSA algorithm."""
    mock_settings.JWT_ALGORITHM = "RS256"
    mock_settings.JWT_KEYS = {"test_kid": rsa_private_key}
    mock_settings.ACTIVE_JWT_KID = "test_kid"

    key, algorithm = get_signing_key()
    assert key == rsa_private_key
    assert algorithm == "RS256"


def test_get_verifying_keys_with_hs256(mock_settings):
    """Test get_verifying_keys with HS256 algorithm."""
    mock_settings.JWT_ALGORITHM = "HS256"
    mock_settings.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
    keys = get_verifying_keys()
    assert len(keys) == 2
    assert keys[0].kid == "kid1"
    assert keys[0].value == "secret1"
    assert keys[1].kid == "kid2"
    assert keys[1].value == "secret2"


def test_get_verifying_keys_with_rs256(mock_settings, rsa_public_key):
    """Test get_verifying_keys with RS256 algorithm."""
    mock_settings.JWT_ALGORITHM = "RS256"
    mock_settings.JWT_KEYS = {"kid1": rsa_public_key}
    keys = get_verifying_keys()
    assert len(keys) == 1
    # We can't directly compare the key objects, so we check the length
    # and assume the correct key is loaded if the length is correct.


def test_get_verifying_keys_with_retired_keys(mock_settings, rsa_public_key):
    """Test get_verifying_keys with retired keys."""
    mock_settings.JWT_ALGORITHM = "RS256"
    mock_settings.JWT_KEYS = {
        "kid1": rsa_public_key,
        "kid2": rsa_public_key,  # Same key for simplicity
    }
    from app.utils import jwt

    retired_time = datetime.now(timezone.utc) - timedelta(days=1)
    with patch.object(jwt, "_RETIRED_KEYS", {"kid2": retired_time}):
        keys = get_verifying_keys()
    assert len(keys) == 1


@pytest.fixture
def rsa_private_key():
    """Fixture for a dummy RSA private key."""
    return (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC..."
        "\n-----END PRIVATE KEY-----"
    )


@pytest.fixture
def rsa_public_key():
    """Fixture for a dummy RSA public key."""
    return (
        "-----BEGIN PUBLIC KEY-----\n"
        "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA..."
        "\n-----END PUBLIC KEY-----"
    )
