from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.schemas.jwt import JWTPayload


def test_valid_payload():
    now = int(datetime.now(timezone.utc).timestamp())
    payload = JWTPayload(
        sub=uuid4(),
        exp=now + 60,
        iat=now,
        jti="abc",
        roles=["user"],
        attributes={"k": "v"},
    )
    assert payload.roles == ["user"]
    assert payload.attributes["k"] == "v"


def test_invalid_uuid():
    now = int(datetime.now(timezone.utc).timestamp())
    with pytest.raises(Exception):
        JWTPayload(sub="not-a-uuid", exp=now + 60, iat=now, jti="x")


def test_expired_token():
    now = int(datetime.now(timezone.utc).timestamp())
    with pytest.raises(Exception):
        JWTPayload(sub=uuid4(), exp=now - 10, iat=now - 20, jti="x")
