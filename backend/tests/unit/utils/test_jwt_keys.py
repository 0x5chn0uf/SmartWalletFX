"""Unit tests for utils.jwt_keys.format_public_key_to_jwk"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import ConfigurationService
from app.utils.jwt_keys import (
    _b64url_uint,
    format_public_key_to_jwk,
    get_verifying_keys,
)


@pytest.fixture
def mock_settings(monkeypatch):
    """Return a proxy whose attribute-writes update ConfigurationService."""

    class _Proxy:
        def __setattr__(self, name, value):
            monkeypatch.setattr(ConfigurationService, name, value, raising=False)

    # Return an instance that test methods can assign to
    return _Proxy()


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


def test_get_verifying_keys_with_rs256(mock_settings):
    """Test get_verifying_keys with RS256 algorithm."""
    # Setup
    mock_settings.JWT_ALGORITHM = "RS256"
    mock_settings.JWT_KEYS = {
        "kid1": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzyis1ZjfNB0bBgKFMSv\nvkTtwlvBsaJq7S5wA+kzeVOVpVWwkWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHc\naT92whREFpLv9cj5lTeJSibyr/Mrm/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIy\ntvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0\ne+lf4s4OxQawWD79J9/5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWb\nV6L11BWkpzGXSW4Hv43qa+GSYOD2QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9\nMwIDAQAB\n-----END PUBLIC KEY-----",
    }

    # Execute
    keys = get_verifying_keys()

    # Verify
    assert len(keys) == 1
    assert keys[0].kid == "kid1"
    assert keys[0].value == mock_settings.JWT_KEYS["kid1"]
    assert keys[0].retired_at is None


def test_get_verifying_keys_with_retired_keys(mock_settings):
    """Test get_verifying_keys with retired keys."""
    # Setup
    mock_settings.JWT_ALGORITHM = "RS256"
    mock_settings.JWT_KEYS = {
        "kid1": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzyis1ZjfNB0bBgKFMSv\nvkTtwlvBsaJq7S5wA+kzeVOVpVWwkWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHc\naT92whREFpLv9cj5lTeJSibyr/Mrm/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIy\ntvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0\ne+lf4s4OxQawWD79J9/5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWb\nV6L11BWkpzGXSW4Hv43qa+GSYOD2QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9\nMwIDAQAB\n-----END PUBLIC KEY-----",
        "kid2": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzyis1ZjfNB0bBgKFMSv\nvkTtwlvBsaJq7S5wA+kzeVOVpVWwkWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHc\naT92whREFpLv9cj5lTeJSibyr/Mrm/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIy\ntvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0\ne+lf4s4OxQawWD79J9/5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWb\nV6L11BWkpzGXSW4Hv43qa+GSYOD2QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9\nMwIDAQAB\n-----END PUBLIC KEY-----",
    }

    # Mock the _RETIRED_KEYS dictionary in jwt module
    from app.utils import jwt

    retired_time = datetime.now(timezone.utc) - timedelta(days=1)  # Retired 1 day ago
    with patch.object(jwt, "_RETIRED_KEYS", {"kid2": retired_time}):
        # Execute
        keys = get_verifying_keys()

    # Verify
    assert len(keys) == 1  # Only kid1 should be returned
    assert keys[0].kid == "kid1"
