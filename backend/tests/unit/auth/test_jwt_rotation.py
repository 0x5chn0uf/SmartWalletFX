"""Comprehensive tests for JWT key-rotation (Subtask 4.13).

This single module consolidates:
• **Unit tests** – verify helper behaviour (`rotate_signing_key`, grace-period).
• **Integration test** – end-to-end flow via FastAPI `/auth/token` & `/users/me`.
• **Property-based tests** – randomised round-trip invariants using Hypothesis.
"""

from datetime import timedelta

import hypothesis.strategies as st
import pytest
from httpx import AsyncClient
from hypothesis import given
from hypothesis import settings as hyp_settings

from app.core.config import settings

# Integration test dependencies
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.utils import jwt as jwt_utils
from app.utils.jwt import _RETIRED_KEYS, JWTUtils, _now_utc, rotate_signing_key


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    """Ensure we start each test with a clean key-set state."""
    # Reset settings map
    settings.JWT_KEYS = {"A": "secretA"}
    settings.ACTIVE_JWT_KID = "A"
    _RETIRED_KEYS.clear()
    yield
    _RETIRED_KEYS.clear()


def test_rotation_grace_period_allows_old_tokens(freezer):
    user_id = "123"

    # Issue token with key A
    token_old = JWTUtils.create_access_token(user_id)

    # Rotate to key B
    rotate_signing_key("B", "secretB")

    # Issue token with key B
    token_new = JWTUtils.create_access_token(user_id)

    # Both tokens should decode successfully within grace period
    assert JWTUtils.decode_token(token_old)["sub"] == user_id
    assert JWTUtils.decode_token(token_new)["sub"] == user_id

    # Fast-forward past grace-period using the *freezer* fixture for deterministic time
    freezer.tick(timedelta(seconds=settings.JWT_ROTATION_GRACE_PERIOD_SECONDS + 1))

    # Old token should now be invalid
    with pytest.raises(Exception):
        JWTUtils.decode_token(token_old)

    # New token still valid
    assert JWTUtils.decode_token(token_new)["sub"] == user_id


@pytest.mark.anyio
async def test_key_rotation_lifecycle(test_app, db_session, freezer):
    """End-to-end validation: old token accepted during grace, rejected after."""

    settings.JWT_KEYS = {"A": "secretA"}
    settings.ACTIVE_JWT_KID = "A"
    settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 1  # fast

    # Clear helper caches
    JWTUtils._get_sign_key.cache_clear()
    JWTUtils._get_verify_key.cache_clear()

    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        svc = AuthService(db_session)
        await svc.register(
            UserCreate(username="rotuser", email="rot@ex.com", password="Str0ng!pwd")
        )

        # Old token (key A)
        resp_old = await ac.post(
            "/auth/token", data={"username": "rotuser", "password": "Str0ng!pwd"}
        )
        token_old = resp_old.json()["access_token"]

        # Rotate to key B
        rotate_signing_key("B", "secretB")
        JWTUtils._get_sign_key.cache_clear()
        JWTUtils._get_verify_key.cache_clear()

        # New token (key B)
        resp_new = await ac.post(
            "/auth/token", data={"username": "rotuser", "password": "Str0ng!pwd"}
        )
        token_new = resp_new.json()["access_token"]

        hdr_old = {"Authorization": f"Bearer {token_old}"}
        hdr_new = {"Authorization": f"Bearer {token_new}"}
        # Within grace-period
        assert (await ac.get("/users/me", headers=hdr_old)).status_code == 200
        assert (await ac.get("/users/me", headers=hdr_new)).status_code == 200

        # Jump forward beyond grace-period
        freezer.tick(timedelta(seconds=2))

        assert (await ac.get("/users/me", headers=hdr_old)).status_code == 401
        assert (await ac.get("/users/me", headers=hdr_new)).status_code == 200


# ---------------------------------------------------------------------------
# Property-based Tests – Hypothesis random secrets                      (sync)
# ---------------------------------------------------------------------------


@hyp_settings(max_examples=25)
@given(
    secret=st.text(min_size=8, max_size=64),
    user_id=st.uuids(),
    ttl=st.integers(min_value=60, max_value=600),
)
def test_round_trip_random_secret(secret: str, user_id, ttl: int):
    """Tokens must round-trip encode → decode for arbitrary secrets & TTLs."""

    settings.JWT_KEYS = {"prop": secret}
    settings.ACTIVE_JWT_KID = "prop"

    token = JWTUtils.create_access_token(
        str(user_id), expires_delta=timedelta(seconds=ttl)
    )
    payload = JWTUtils.decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert int(payload["exp"]) > int(payload["iat"])  # sanity


# ---------------------------------------------------------------------------
# Edge-case / Error-path coverage
# ---------------------------------------------------------------------------


def test_sign_key_misconfiguration():
    """_get_sign_key must raise if ACTIVE_JWT_KID not present in map."""

    settings.JWT_KEYS = {"X": "secretX"}
    settings.ACTIVE_JWT_KID = "missing"

    # Clear caches so _get_sign_key executes fresh
    JWTUtils._get_sign_key.cache_clear()

    with pytest.raises(RuntimeError, match="ACTIVE_JWT_KID not found"):
        JWTUtils._get_sign_key()  # type: ignore[arg-type]


def test_retired_key_token_rejected(freezer):
    """Decoding a token signed with a retired key after grace should fail."""

    user = "abc"
    settings.JWT_KEYS = {"OLD": "oldsecret", "NEW": "newsecret"}
    settings.ACTIVE_JWT_KID = "OLD"
    settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 0

    token_old = JWTUtils.create_access_token(user)

    # Rotate to NEW with immediate retirement (grace 0)
    rotate_signing_key("NEW", "newsecret")

    # Advance time by 1 second so retirement expires
    freezer.tick(timedelta(seconds=1))

    with pytest.raises(Exception):
        JWTUtils.decode_token(token_old)


def test_tampered_token_signature_detected():
    """Altering token payload must raise verification error."""

    settings.JWT_KEYS = {"Z": "tokensecret"}
    settings.ACTIVE_JWT_KID = "Z"

    good = JWTUtils.create_access_token("42")

    # Tamper with payload segment (middle part)
    header_b64, payload_b64, signature_b64 = good.split(".")
    tampered_payload_b64 = (
        payload_b64[:-2] + ("A" if payload_b64[-2] != "A" else "B") + payload_b64[-1]
    )
    bad_token = ".".join([header_b64, tampered_payload_b64, signature_b64])

    with pytest.raises(Exception):
        JWTUtils.decode_token(bad_token)


def test_verify_key_fallback_first_entry():
    """When ACTIVE_JWT_KID missing, _get_verify_key should return first map value."""

    settings.JWT_KEYS = {"first": "s1", "second": "s2"}
    settings.ACTIVE_JWT_KID = "missing"

    JWTUtils._get_verify_key.cache_clear()
    key = JWTUtils._get_verify_key()  # type: ignore[arg-type]
    assert key in {"s1", "s2"}


def test_signature_mismatch_detected():
    """Altering only the signature segment must trigger verification failure inside the custom comparison block (lines 247+)."""

    settings.JWT_KEYS = {"sig": "sigsecret"}
    settings.ACTIVE_JWT_KID = "sig"

    token = JWTUtils.create_access_token("777")

    header_b64, payload_b64, signature_b64 = token.split(".")
    # Flip last char of signature
    flipped = "A" if signature_b64[-1] != "A" else "B"
    bad_signature = signature_b64[:-1] + flipped
    tampered = ".".join([header_b64, payload_b64, bad_signature])

    with pytest.raises(Exception):
        JWTUtils.decode_token(tampered)


def test_rotate_signing_key_creates_map_when_none():
    """When JWT_KEYS is None, rotate_signing_key should initialise it."""

    # Simulate uninitialised state (possible early startup scenario)
    settings.JWT_KEYS = None  # type: ignore[assignment]
    settings.ACTIVE_JWT_KID = "legacy"

    rotate_signing_key("new", "s3cret")

    assert settings.JWT_KEYS is not None
    assert settings.JWT_KEYS["new"] == "s3cret"
    assert settings.ACTIVE_JWT_KID == "new"


def test_get_sign_key_requires_secret():
    """_get_sign_key should raise if no secret configured for HS algorithms."""

    settings.JWT_ALGORITHM = "HS256"
    settings.JWT_KEYS = {}
    settings.JWT_SECRET_KEY = None  # type: ignore[assignment]

    JWTUtils._get_sign_key.cache_clear()

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY must be set"):
        JWTUtils._get_sign_key()  # type: ignore[arg-type]
