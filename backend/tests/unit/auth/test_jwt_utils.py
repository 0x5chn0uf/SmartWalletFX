from datetime import timedelta

import pytest
from jose.exceptions import ExpiredSignatureError

from app.core.config import settings
from app.utils.jwt import JWTUtils


def _configure_hs256(monkeypatch):
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "test-secret", raising=False)


def test_jwt_round_trip(monkeypatch):
    _configure_hs256(monkeypatch)
    token = JWTUtils.create_access_token("user-123", expires_delta=timedelta(minutes=1))
    payload = JWTUtils.decode_token(token)
    assert payload["sub"] == "user-123"


def test_jwt_expired_token(monkeypatch):
    _configure_hs256(monkeypatch)
    token = JWTUtils.create_access_token(
        "user-123", expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(ExpiredSignatureError):
        JWTUtils.decode_token(token)
