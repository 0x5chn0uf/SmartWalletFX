from datetime import timedelta

import pytest
from jose.exceptions import ExpiredSignatureError, JWTError

from app.core.config import settings
from app.utils.jwt import JWTUtils
from uuid import uuid4


def _configure_hs256(monkeypatch):
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "test-secret", raising=False)


def test_jwt_round_trip(monkeypatch):
    _configure_hs256(monkeypatch)
    user_id = uuid4()
    token = JWTUtils.create_access_token(str(user_id), expires_delta=timedelta(minutes=1))
    payload = JWTUtils.decode_token(token)
    assert payload["sub"] == str(user_id)


def test_jwt_expired_token(monkeypatch):
    _configure_hs256(monkeypatch)
    token = JWTUtils.create_access_token(
        str(uuid4()), expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(ExpiredSignatureError):
        JWTUtils.decode_token(token)


def test_jwt_round_trip_with_claims(monkeypatch):
    """Round-trip with additional claims like `role` should succeed."""
    _configure_hs256(monkeypatch)
    user_id = uuid4()
    token = JWTUtils.create_access_token(str(user_id), additional_claims={"role": "admin"})
    payload = JWTUtils.decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "admin"
    assert "jti" in payload


def test_jwt_invalid_token(monkeypatch):
    """Tampering with the token should raise JWTError."""
    _configure_hs256(monkeypatch)
    token = JWTUtils.create_access_token(str(uuid4()))
    corrupted = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises((JWTError, Exception)) as exc_info:
        JWTUtils.decode_token(corrupted)
    # Verify it's a JWT-related exception
    assert (
        "JWT" in str(type(exc_info.value).__name__)
        or "jwt" in str(type(exc_info.value).__name__).lower()
    )
