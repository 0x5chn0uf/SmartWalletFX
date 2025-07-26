"""Comprehensive unit tests for JWT utilities."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, mock_open, patch

import pytest
from jose import ExpiredSignatureError, JWSError, JWTError

from app.core.config import Configuration
from app.utils.jwt import (
    _RETIRED_KEYS,
    JWTUtils,
    _now_utc,
    _to_text,
    rotate_signing_key,
)
from app.utils.logging import Audit


@pytest.fixture
def mock_config():
    """Return a mocked Configuration instance."""
    config = MagicMock(spec=Configuration)
    # Set default values
    config.JWT_ALGORITHM = "HS256"
    config.JWT_KEYS = None
    config.ACTIVE_JWT_KID = None
    config.JWT_SECRET_KEY = "insecure-test-key"
    config.JWT_PRIVATE_KEY_PATH = None
    config.JWT_PUBLIC_KEY_PATH = None
    config.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    config.REFRESH_TOKEN_EXPIRE_DAYS = 7
    config.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600
    return config


class TestJWTUtils:
    """Test JWT utility functions."""

    def setup_method(self):
        """Clear retired keys before each test."""
        _RETIRED_KEYS.clear()
        # LRU caches were removed from JWT methods

    @pytest.mark.unit
    def test_get_sign_key_hs256_with_keys(self, mock_config):
        """Test _get_sign_key with HS256 and JWT_KEYS configured."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_config.ACTIVE_JWT_KID = "kid1"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils._get_sign_key()
        assert result == "secret1"

    @pytest.mark.unit
    def test_get_sign_key_hs256_without_keys(self, mock_config):
        """Test _get_sign_key with HS256 and no JWT_KEYS."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = None
        mock_config.JWT_SECRET_KEY = "fallback_secret"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils._get_sign_key()
        assert result == "fallback_secret"

    @pytest.mark.unit
    def test_get_sign_key_hs256_missing_active_kid(self, mock_config):
        """Test _get_sign_key with missing ACTIVE_JWT_KID."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_config.ACTIVE_JWT_KID = "missing_kid"

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(RuntimeError, match="ACTIVE_JWT_KID not found"):
            jwt_utils._get_sign_key()

    @pytest.mark.unit
    def test_get_sign_key_hs256_missing_secret(self, mock_config):
        """Test _get_sign_key with missing JWT_SECRET_KEY."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = None
        mock_config.JWT_SECRET_KEY = None

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY must be set"):
            jwt_utils._get_sign_key()

    @patch("builtins.open", new_callable=mock_open, read_data="private_key_content")
    @pytest.mark.unit
    def test_get_sign_key_rs256(self, mock_file, mock_config):
        """Test _get_sign_key with RS256 algorithm."""
        mock_config.JWT_ALGORITHM = "RS256"
        mock_config.JWT_PRIVATE_KEY_PATH = "/path/to/private.key"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils._get_sign_key()
        assert result == "private_key_content"
        mock_file.assert_called_once_with("/path/to/private.key", "r", encoding="utf-8")

    @pytest.mark.unit
    def test_get_sign_key_rs256_missing_private_key_path(self, mock_config):
        """Test _get_sign_key with RS256 and missing private key path."""
        mock_config.JWT_ALGORITHM = "RS256"
        mock_config.JWT_PRIVATE_KEY_PATH = None

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(RuntimeError, match="JWT_PRIVATE_KEY_PATH must be set"):
            jwt_utils._get_sign_key()

    @pytest.mark.unit
    def test_get_sign_key_unsupported_algorithm(self, mock_config):
        """Test _get_sign_key with unsupported algorithm."""
        mock_config.JWT_ALGORITHM = "ES256"

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(RuntimeError, match="Unsupported JWT_ALGORITHM"):
            jwt_utils._get_sign_key()

    @pytest.mark.unit
    def test_get_verify_key_hs256_with_keys(self, mock_config):
        """Test _get_verify_key with HS256 and JWT_KEYS."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_config.ACTIVE_JWT_KID = "kid1"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils._get_verify_key()
        assert result == "secret1"

    @pytest.mark.unit
    def test_get_verify_key_hs256_fallback_to_first_key(self, mock_config):
        """Test _get_verify_key falls back to first key when active KID not found."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_config.ACTIVE_JWT_KID = "missing_kid"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils._get_verify_key()
        assert result == "secret1"  # First key in dict

    @pytest.mark.unit
    def test_get_verify_key_hs256_fallback_to_signing_key(self, mock_config):
        """Test _get_verify_key falls back to signing key when no JWT_KEYS."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = None
        mock_config.JWT_SECRET_KEY = "fallback_secret"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils._get_verify_key()
        assert result == "fallback_secret"

    @patch("builtins.open", new_callable=mock_open, read_data="public_key_content")
    @pytest.mark.unit
    def test_get_verify_key_rs256(self, mock_file, mock_config):
        """Test _get_verify_key with RS256 algorithm."""
        mock_config.JWT_ALGORITHM = "RS256"
        mock_config.JWT_PUBLIC_KEY_PATH = "/path/to/public.key"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils._get_verify_key()
        assert result == "public_key_content"
        mock_file.assert_called_once_with("/path/to/public.key", "r", encoding="utf-8")

    @pytest.mark.unit
    def test_get_verify_key_rs256_missing_public_key_path(self, mock_config):
        """Test _get_verify_key with RS256 and missing public key path."""
        mock_config.JWT_ALGORITHM = "RS256"
        mock_config.JWT_PUBLIC_KEY_PATH = None

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(RuntimeError, match="JWT_PUBLIC_KEY_PATH must be set"):
            jwt_utils._get_verify_key()

    @pytest.mark.unit
    def test_get_verify_key_unsupported_algorithm(self, mock_config):
        """Test _get_verify_key with unsupported algorithm."""
        mock_config.JWT_ALGORITHM = "ES256"

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(RuntimeError, match="Unsupported JWT_ALGORITHM"):
            jwt_utils._get_verify_key()

    @patch("app.utils.jwt.jwt.encode")
    @pytest.mark.unit
    def test_create_access_token_success(self, mock_encode, mock_config):
        """Test successful access token creation."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_config.ACTIVE_JWT_KID = "kid1"
        mock_config.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_encode.return_value = "encoded_token"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils.create_access_token("user123")

        assert result == "encoded_token"
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args
        assert call_args[0][1] == "secret1"  # signing key
        assert call_args[1]["algorithm"] == "HS256"
        assert call_args[1]["headers"] == {"kid": "kid1"}

    @patch("app.utils.jwt.jwt.encode")
    @pytest.mark.unit
    def test_create_access_token_with_additional_claims(self, mock_encode, mock_config):
        """Test access token creation with additional claims."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_config.ACTIVE_JWT_KID = "kid1"
        mock_config.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_encode.return_value = "encoded_token"

        additional_claims = {"role": "admin", "permissions": ["read", "write"]}
        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils.create_access_token(
            "user123", additional_claims=additional_claims
        )

        assert result == "encoded_token"
        call_args = mock_encode.call_args
        payload = call_args[0][0]
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]

    @patch("app.utils.jwt.jwt.encode")
    @pytest.mark.unit
    def test_create_access_token_with_custom_expiry(self, mock_encode, mock_config):
        """Test access token creation with custom expiry."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_config.ACTIVE_JWT_KID = "kid1"
        mock_encode.return_value = "encoded_token"

        custom_expiry = timedelta(hours=2)
        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils.create_access_token("user123", expires_delta=custom_expiry)

        assert result == "encoded_token"
        call_args = mock_encode.call_args
        payload = call_args[0][0]
        # Verify expiry is set correctly
        assert "exp" in payload
        assert "iat" in payload

    @patch("app.utils.jwt.jwt.encode")
    @pytest.mark.unit
    def test_create_access_token_retry_with_alt_key_representation(
        self, mock_encode, mock_config
    ):
        """Test access token creation with retry using alternate key representation."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_config.ACTIVE_JWT_KID = "kid1"
        mock_config.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        # First call fails, second succeeds
        mock_encode.side_effect = [JWTError("Key format error"), "encoded_token"]

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils.create_access_token("user123")

        assert result == "encoded_token"
        assert mock_encode.call_count == 2

    @patch("app.utils.jwt.jwt.encode")
    @pytest.mark.unit
    def test_create_refresh_token_success(self, mock_encode, mock_config):
        """Test successful refresh token creation."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_config.ACTIVE_JWT_KID = "kid1"
        mock_config.REFRESH_TOKEN_EXPIRE_DAYS = 7
        mock_encode.return_value = "refresh_token"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils.create_refresh_token("user123")

        assert result == "refresh_token"
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args
        payload = call_args[0][0]
        assert payload["type"] == "refresh"
        assert payload["sub"] == "user123"

    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @pytest.mark.unit
    def test_decode_token_success(self, mock_get_header, mock_decode, mock_config):
        """Test successful token decoding."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_get_header.return_value = {"kid": "kid1"}

        # Create a valid payload that matches the JWTPayload schema
        user_id = str(uuid.uuid4())
        now = int(datetime.now(timezone.utc).timestamp())
        mock_decode.return_value = {
            "sub": user_id,
            "jti": "token123",
            "iat": now,
            "exp": now + 3600,  # 1 hour in the future
            "type": "access",
            "roles": ["user"],
            "attributes": {},
        }

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils.decode_token("valid_token")

        assert result["sub"] == user_id
        assert result["jti"] == "token123"
        assert result["exp"] == now + 3600
        mock_get_header.assert_called_once_with("valid_token")
        mock_decode.assert_called_once()

    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @pytest.mark.unit
    def test_decode_token_expired_signature(
        self, mock_get_header, mock_decode, mock_config
    ):
        """Test token decoding with expired signature."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_get_header.return_value = {"kid": "kid1"}
        mock_decode.side_effect = ExpiredSignatureError("Token expired")

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(ExpiredSignatureError, match="Token expired"):
            jwt_utils.decode_token("expired_token")

    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @pytest.mark.unit
    def test_decode_token_jwt_error(self, mock_get_header, mock_decode, mock_config):
        """Test token decoding with JWT error."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_get_header.return_value = {"kid": "kid1"}
        mock_decode.side_effect = JWTError("Invalid token")

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(JWTError, match="Invalid token"):
            jwt_utils.decode_token("invalid_token")

    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @patch("app.utils.jwt._now_utc")
    @pytest.mark.unit
    def test_decode_token_with_retired_keys(
        self, mock_now_utc, mock_get_header, mock_decode, mock_config
    ):
        """Test token decoding with retired keys."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_get_header.return_value = {"kid": "kid2"}
        mock_decode.return_value = {"sub": "user123", "type": "access"}

        # Set up retired key with expiry in the past
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        mock_now_utc.return_value = datetime.now(timezone.utc)
        _RETIRED_KEYS["kid2"] = past_time

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(
            ExpiredSignatureError, match="Token signed with retired key"
        ):
            jwt_utils.decode_token("token_with_retired_key")

    @patch("app.utils.jwt.jwt.encode")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @pytest.mark.unit
    def test_decode_token_with_jwk_error_and_retry(
        self, mock_get_header, mock_decode, mock_encode, mock_config
    ):
        """Test token decoding with successful decode on first try."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_get_header.return_value = {"kid": "kid1"}

        # Create a valid payload that matches the JWTPayload schema
        user_id = str(uuid.uuid4())
        now = int(datetime.now(timezone.utc).timestamp())
        valid_payload = {
            "sub": user_id,
            "jti": "token123",
            "iat": now,
            "exp": now + 3600,  # 1 hour in the future
            "type": "access",
            "roles": ["user"],
            "attributes": {},
        }

        # Successful decode on first try
        mock_decode.return_value = valid_payload

        # Mock the encode method to return a consistent signature for verification
        mock_encode.return_value = "header.payload.signature"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils.decode_token("header.payload.signature")

        assert result["sub"] == user_id
        assert result["jti"] == "token123"
        assert result["exp"] == now + 3600
        assert mock_decode.call_count == 1

    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @pytest.mark.unit
    def test_decode_token_all_keys_fail(
        self, mock_get_header, mock_decode, mock_config
    ):
        """Test token decoding when all keys fail."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_get_header.return_value = {"kid": "kid1"}
        # Both original and alternate key representations fail
        mock_decode.side_effect = JWSError("JWK error")

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(JWSError, match="JWK error"):
            jwt_utils.decode_token("token_with_all_keys_failing")

    @patch("app.utils.jwt.jwt.encode")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @pytest.mark.unit
    def test_decode_token_signature_verification_failure(
        self, mock_get_header, mock_decode, mock_encode, mock_config
    ):
        """Test token decoding with signature verification failure during re-encoding check."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_get_header.return_value = {"kid": "kid1"}

        # Valid payload for initial decode
        user_id = str(uuid.uuid4())
        now = int(datetime.now(timezone.utc).timestamp())
        valid_payload = {
            "sub": user_id,
            "jti": "token123",
            "iat": now,
            "exp": now + 3600,
            "type": "access",
            "roles": ["user"],
            "attributes": {},
        }
        mock_decode.return_value = valid_payload

        # Mock encode to return a different signature to trigger verification failure
        mock_encode.return_value = "header.payload.different_signature"

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(JWTError, match="Signature verification failed"):
            jwt_utils.decode_token("header.payload.original_signature")

    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @pytest.mark.unit
    def test_decode_token_missing_sub_claim(
        self, mock_get_header, mock_decode, mock_config
    ):
        """Test token decoding with missing sub claim."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_get_header.return_value = {"kid": "kid1"}

        # Create an invalid payload without the required 'sub' field
        now = int(datetime.now(timezone.utc).timestamp())
        mock_decode.return_value = {
            "jti": "token123",
            "iat": now,
            "exp": now + 3600,
            "type": "access",
        }  # Missing 'sub'

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(
            JWTError, match="Token payload is missing required 'sub' claim"
        ):
            jwt_utils.decode_token("token_missing_sub")

    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @pytest.mark.unit
    def test_decode_token_empty_sub_claim(
        self, mock_get_header, mock_decode, mock_config
    ):
        """Test token decoding with empty sub claim."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_get_header.return_value = {"kid": "kid1"}

        # Create an invalid payload with empty 'sub' field
        now = int(datetime.now(timezone.utc).timestamp())
        mock_decode.return_value = {
            "sub": "",  # Empty 'sub'
            "jti": "token123",
            "iat": now,
            "exp": now + 3600,
            "type": "access",
        }

        jwt_utils = JWTUtils(mock_config, Audit())
        with pytest.raises(
            JWTError, match="Token payload is missing required 'sub' claim"
        ):
            jwt_utils.decode_token("token_empty_sub")

    @patch("app.utils.jwt.jwt.encode")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @pytest.mark.unit
    def test_decode_token_fallback_to_default_key(
        self, mock_get_header, mock_decode, mock_encode, mock_config
    ):
        """Test token decoding with fallback to default key when kid not found."""
        mock_config.JWT_ALGORITHM = "HS256"
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_config.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "unknown_kid"}

        # Create a valid payload that matches the JWTPayload schema
        user_id = str(uuid.uuid4())
        now = int(datetime.now(timezone.utc).timestamp())
        valid_payload = {
            "sub": user_id,
            "jti": "token123",
            "iat": now,
            "exp": now + 3600,  # 1 hour in the future
            "type": "access",
            "roles": ["user"],
            "attributes": {},
        }

        # When unknown kid is used, it should fallback to the verify key which uses the first key
        mock_decode.return_value = valid_payload
        mock_encode.return_value = "header.payload.signature"

        jwt_utils = JWTUtils(mock_config, Audit())
        result = jwt_utils.decode_token("header.payload.signature")

        assert result["sub"] == user_id
        assert result["jti"] == "token123"
        assert result["exp"] == now + 3600

    @pytest.mark.unit
    def test_load_key_success(self, mock_config):
        """Test loading a key from file."""
        with patch("builtins.open", mock_open(read_data="key_content")):
            jwt_utils = JWTUtils(mock_config, Audit())
            result = jwt_utils._load_key("key_path")
            assert result == "key_content"

    @pytest.mark.unit
    def test_to_text_with_string(self):
        """Test _to_text with string input."""
        assert _to_text("test_string") == "test_string"

    @pytest.mark.unit
    def test_to_text_with_bytes(self):
        """Test _to_text with bytes input."""
        assert _to_text(b"test_bytes") == "test_bytes"

    @pytest.mark.unit
    def test_now_utc(self):
        """Test _now_utc returns datetime in UTC timezone."""
        result = _now_utc()
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc


class TestRotateSigningKey:
    """Test the rotate_signing_key function."""

    def setup_method(self):
        """Clear retired keys before each test."""
        _RETIRED_KEYS.clear()

    @patch("app.utils.logging.Audit.info")
    @pytest.mark.unit
    def test_rotate_signing_key_new_key(self, mock_audit, mock_config):
        """Test rotating to a new signing key."""
        mock_config.JWT_KEYS = {"old_kid": "old_secret"}
        mock_config.ACTIVE_JWT_KID = "old_kid"
        mock_config.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600

        # Use the mock_config in the function call
        rotate_signing_key("new_kid", "new_secret", mock_config)

        assert mock_config.ACTIVE_JWT_KID == "new_kid"
        assert mock_config.JWT_KEYS == {
            "old_kid": "old_secret",
            "new_kid": "new_secret",
        }
        assert "old_kid" in _RETIRED_KEYS
        mock_audit.assert_called_once()

    @patch("app.utils.logging.Audit.info")
    @pytest.mark.unit
    def test_rotate_signing_key_same_key(self, mock_audit, mock_config):
        """Test rotating to the same key ID."""
        mock_config.JWT_KEYS = {"kid1": "old_secret"}
        mock_config.ACTIVE_JWT_KID = "kid1"

        # Use the mock_config in the function call
        rotate_signing_key("kid1", "new_secret", mock_config)

        assert mock_config.ACTIVE_JWT_KID == "kid1"
        assert mock_config.JWT_KEYS == {"kid1": "new_secret"}
        assert "kid1" not in _RETIRED_KEYS
        mock_audit.assert_called_once()

    @patch("app.utils.logging.Audit.info")
    @pytest.mark.unit
    def test_rotate_signing_key_no_existing_keys(self, mock_audit, mock_config):
        """Test rotating when no existing keys."""
        mock_config.JWT_KEYS = None
        mock_config.ACTIVE_JWT_KID = None

        # Use the mock_config in the function call
        rotate_signing_key("new_kid", "new_secret", mock_config)

        assert mock_config.ACTIVE_JWT_KID == "new_kid"
        assert mock_config.JWT_KEYS == {"new_kid": "new_secret"}
        assert not _RETIRED_KEYS
        mock_audit.assert_called_once()

    @patch("app.utils.logging.Audit.info")
    @pytest.mark.unit
    def test_rotate_signing_key_old_key_not_in_keys(self, mock_audit, mock_config):
        """Test rotating when old key not in keys."""
        mock_config.JWT_KEYS = {"kid1": "secret1"}
        mock_config.ACTIVE_JWT_KID = "missing_kid"

        # Use the mock_config in the function call
        rotate_signing_key("new_kid", "new_secret", mock_config)

        assert mock_config.ACTIVE_JWT_KID == "new_kid"
        assert mock_config.JWT_KEYS == {"kid1": "secret1", "new_kid": "new_secret"}
        assert "missing_kid" not in _RETIRED_KEYS
        mock_audit.assert_called_once()
