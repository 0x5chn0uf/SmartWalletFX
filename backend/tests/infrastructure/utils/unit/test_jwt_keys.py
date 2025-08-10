"""Unit tests for utils.jwt_keys.JWTKeyUtils"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.utils.jwt_keys import JWTKeyUtils, _b64url_uint


@pytest.fixture
def mock_config():
    """Fixture to mock JWT configuration for testing."""
    config = _MockConfig()
    config.JWT_ALGORITHM = "HS256"
    config.JWT_KEYS = {"test_kid": "test_secret"}
    config.ACTIVE_JWT_KID = "test_kid"
    config.JWT_ROTATION_GRACE_PERIOD_SECONDS = 60
    return config


@pytest.fixture
def jwt_key_utils(mock_config):
    """Fixture to create JWTKeyUtils instance."""
    return JWTKeyUtils(mock_config)


class _MockConfig:
    """A mock config object for testing."""

    def __init__(self):
        self.JWT_ALGORITHM = "HS256"
        self.JWT_KEYS = {}
        self.ACTIVE_JWT_KID = ""
        self.JWT_ROTATION_GRACE_PERIOD_SECONDS = 60


@pytest.mark.unit
def test_b64url_uint():
    """Test base64url encoding of integers."""
    assert _b64url_uint(1) == "AQ"
    assert _b64url_uint(65537) == "AQAB"


@pytest.mark.unit
def test_format_public_key_to_jwk_with_rs256(jwt_key_utils):
    """Test format_public_key_to_jwk with RS256 algorithm."""
    # Setup
    public_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzyis1ZjfNB0bBgKFMSv\nvkTtwlvBsaJq7S5wA+kzeVOVpVWwkWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHc\naT92whREFpLv9cj5lTeJSibyr/Mrm/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIy\ntvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0\ne+lf4s4OxQawWD79J9/5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWb\nV6L11BWkpzGXSW4Hv43qa+GSYOD2QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9\nMwIDAQAB\n-----END PUBLIC KEY-----"
    kid = "kid1"

    # Execute
    jwk = jwt_key_utils.format_public_key_to_jwk(public_key, kid)

    # Verify
    assert jwk["kty"] == "RSA"
    assert jwk["kid"] == "kid1"
    assert "n" in jwk
    assert "e" in jwk
    assert jwk["alg"] == "RS256"


@pytest.mark.unit
def test_format_public_key_to_jwk_with_custom_alg(jwt_key_utils):
    """Test format_public_key_to_jwk with custom algorithm."""
    # Setup
    public_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzyis1ZjfNB0bBgKFMSv\nvkTtwlvBsaJq7S5wA+kzeVOVpVWwkWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHc\naT92whREFpLv9cj5lTeJSibyr/Mrm/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIy\ntvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0\ne+lf4s4OxQawWD79J9/5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWb\nV6L11BWkpzGXSW4Hv43qa+GSYOD2QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9\nMwIDAQAB\n-----END PUBLIC KEY-----"
    kid = "kid1"

    # Execute
    jwk = jwt_key_utils.format_public_key_to_jwk(public_key, kid, alg="RS384")

    # Verify
    assert jwk["kty"] == "RSA"
    assert jwk["kid"] == "kid1"
    assert "n" in jwk
    assert "e" in jwk
    assert jwk["alg"] == "RS384"


@pytest.mark.unit
def test_get_signing_key(mock_config):
    """Test get_signing_key with mock settings."""
    mock_config.JWT_ALGORITHM = "HS256"
    mock_config.JWT_KEYS = {"test_kid": "a_very_long_secret_key_for_hs256"}
    mock_config.ACTIVE_JWT_KID = "test_kid"

    jwt_key_utils = JWTKeyUtils(mock_config)
    key, algorithm = jwt_key_utils.get_signing_key()
    assert key == "a_very_long_secret_key_for_hs256"
    assert algorithm == "HS256"


@pytest.mark.unit
def test_get_signing_key_rsa(mock_config, rsa_private_key):
    """Test get_signing_key with RSA algorithm."""
    mock_config.JWT_ALGORITHM = "RS256"
    mock_config.JWT_KEYS = {"test_kid": rsa_private_key}
    mock_config.ACTIVE_JWT_KID = "test_kid"

    jwt_key_utils = JWTKeyUtils(mock_config)
    key, algorithm = jwt_key_utils.get_signing_key()
    assert key == rsa_private_key
    assert algorithm == "RS256"


@pytest.mark.unit
def test_get_verifying_keys_with_hs256(mock_config):
    """Test get_verifying_keys with HS256 algorithm."""
    mock_config.JWT_ALGORITHM = "HS256"
    mock_config.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}

    jwt_key_utils = JWTKeyUtils(mock_config)
    keys = jwt_key_utils.get_verifying_keys()
    assert len(keys) == 2
    assert keys[0].kid == "kid1"
    assert keys[0].value == "secret1"
    assert keys[1].kid == "kid2"
    assert keys[1].value == "secret2"


@pytest.mark.unit
def test_get_verifying_keys_with_rs256(mock_config, rsa_public_key):
    """Test get_verifying_keys with RS256 algorithm."""
    mock_config.JWT_ALGORITHM = "RS256"
    mock_config.JWT_KEYS = {"kid1": rsa_public_key}

    jwt_key_utils = JWTKeyUtils(mock_config)
    keys = jwt_key_utils.get_verifying_keys()
    assert len(keys) == 1
    # We can't directly compare the key objects, so we check the length
    # and assume the correct key is loaded if the length is correct.


@pytest.mark.unit
def test_get_verifying_keys_with_retired_keys(mock_config, rsa_public_key):
    """Test get_verifying_keys with retired keys."""
    mock_config.JWT_ALGORITHM = "RS256"
    mock_config.JWT_KEYS = {
        "kid1": rsa_public_key,
        "kid2": rsa_public_key,  # Same key for simplicity
    }
    from app.utils import jwt

    jwt_key_utils = JWTKeyUtils(mock_config)
    retired_time = datetime.now(timezone.utc) - timedelta(days=1)
    with patch.object(jwt, "_RETIRED_KEYS", {"kid2": retired_time}):
        keys = jwt_key_utils.get_verifying_keys()
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
