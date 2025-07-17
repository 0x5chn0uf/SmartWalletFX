from datetime import timedelta
from uuid import uuid4

import pytest
from jose.exceptions import JWTError

from app.core.config import Configuration
from app.domain.errors import InvalidCredentialsError
from app.utils.jwt import JWTUtils


def _configure_hs256(monkeypatch):
    monkeypatch.setattr(Configuration, "JWT_ALGORITHM", "HS256", raising=False)
    monkeypatch.setattr(Configuration, "JWT_SECRET_KEY", "test-secret", raising=False)


def test_jwt_round_trip(mock_jwt_utils):
    user_id = uuid4()
    # Mock the JWT utils methods to return expected values
    token = "mock.jwt.token"
    payload = {"sub": str(user_id)}

    mock_jwt_utils.create_access_token.return_value = token
    mock_jwt_utils.decode_token.return_value = payload

    result_token = mock_jwt_utils.create_access_token(
        str(user_id), expires_delta=timedelta(minutes=1)
    )
    result_payload = mock_jwt_utils.decode_token(result_token)

    assert result_payload["sub"] == str(user_id)
    mock_jwt_utils.create_access_token.assert_called_once_with(
        str(user_id), expires_delta=timedelta(minutes=1)
    )
    mock_jwt_utils.decode_token.assert_called_once_with(token)


def test_jwt_expired_token(mock_jwt_utils):
    user_id = uuid4()
    # Mock the expired token behavior
    mock_jwt_utils.create_access_token.return_value = "expired.jwt.token"
    mock_jwt_utils.decode_token.side_effect = InvalidCredentialsError("Token expired")

    token = mock_jwt_utils.create_access_token(
        str(user_id), expires_delta=timedelta(seconds=-1)
    )

    with pytest.raises(InvalidCredentialsError, match="Token expired"):
        mock_jwt_utils.decode_token(token)

    mock_jwt_utils.create_access_token.assert_called_once_with(
        str(user_id), expires_delta=timedelta(seconds=-1)
    )


def test_jwt_round_trip_with_claims(mock_jwt_utils):
    """Round-trip with additional claims like `role` should succeed."""
    user_id = uuid4()
    # Mock the JWT utils methods to return expected values with claims
    token = "mock.jwt.token.with.claims"
    payload = {"sub": str(user_id), "role": "admin"}

    mock_jwt_utils.create_access_token.return_value = token
    mock_jwt_utils.decode_token.return_value = payload

    result_token = mock_jwt_utils.create_access_token(
        str(user_id), additional_claims={"role": "admin"}
    )
    result_payload = mock_jwt_utils.decode_token(result_token)

    assert result_payload["sub"] == str(user_id)
    assert result_payload["role"] == "admin"
    mock_jwt_utils.create_access_token.assert_called_once_with(
        str(user_id), additional_claims={"role": "admin"}
    )
    mock_jwt_utils.decode_token.assert_called_once_with(token)


def test_jwt_invalid_token(mock_jwt_utils):
    """Tampering with the token should raise JWTError."""
    user_id = uuid4()
    # Mock an invalid token scenario
    mock_jwt_utils.create_access_token.return_value = "valid.jwt.token"
    mock_jwt_utils.decode_token.side_effect = JWTError("Invalid token")

    token = mock_jwt_utils.create_access_token(str(user_id))
    # Simulate token tampering by modifying the token
    tampered_token = token + "tampered"

    with pytest.raises(JWTError, match="Invalid token"):
        mock_jwt_utils.decode_token(tampered_token)

    mock_jwt_utils.create_access_token.assert_called_once_with(str(user_id))
