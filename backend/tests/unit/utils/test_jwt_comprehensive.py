"""Comprehensive unit tests for JWT utilities."""

from datetime import datetime, timedelta, timezone
from unittest.mock import ANY, MagicMock, Mock, mock_open, patch

import pytest
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.utils.jwt import (
    _RETIRED_KEYS,
    JWTUtils,
    _now_utc,
    _to_text,
    rotate_signing_key,
)


class TestJWTUtils:
    """Test JWT utility functions."""

    def setup_method(self):
        """Clear retired keys before each test."""
        _RETIRED_KEYS.clear()
        # Clear LRU caches
        JWTUtils._get_sign_key.cache_clear()
        JWTUtils._get_verify_key.cache_clear()

    @patch("app.utils.jwt.settings")
    def test_get_sign_key_hs256_with_keys(self, mock_settings):
        """Test _get_sign_key with HS256 and JWT_KEYS configured."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_settings.ACTIVE_JWT_KID = "kid1"

        result = JWTUtils._get_sign_key()
        assert result == "secret1"

    @patch("app.utils.jwt.settings")
    def test_get_sign_key_hs256_without_keys(self, mock_settings):
        """Test _get_sign_key with HS256 and no JWT_KEYS."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = None
        mock_settings.JWT_SECRET_KEY = "fallback_secret"

        result = JWTUtils._get_sign_key()
        assert result == "fallback_secret"

    @patch("app.utils.jwt.settings")
    def test_get_sign_key_hs256_missing_active_kid(self, mock_settings):
        """Test _get_sign_key with missing ACTIVE_JWT_KID."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "missing_kid"

        with pytest.raises(RuntimeError, match="ACTIVE_JWT_KID not found"):
            JWTUtils._get_sign_key()

    @patch("app.utils.jwt.settings")
    def test_get_sign_key_hs256_missing_secret(self, mock_settings):
        """Test _get_sign_key with missing JWT_SECRET_KEY."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = None
        mock_settings.JWT_SECRET_KEY = None

        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY must be set"):
            JWTUtils._get_sign_key()

    @patch("app.utils.jwt.settings")
    @patch("builtins.open", new_callable=mock_open, read_data="private_key_content")
    def test_get_sign_key_rs256(self, mock_file, mock_settings):
        """Test _get_sign_key with RS256 algorithm."""
        mock_settings.JWT_ALGORITHM = "RS256"
        mock_settings.JWT_PRIVATE_KEY_PATH = "/path/to/private.key"

        result = JWTUtils._get_sign_key()
        assert result == "private_key_content"
        mock_file.assert_called_once_with("/path/to/private.key", "r", encoding="utf-8")

    @patch("app.utils.jwt.settings")
    def test_get_sign_key_rs256_missing_private_key_path(self, mock_settings):
        """Test _get_sign_key with RS256 and missing private key path."""
        mock_settings.JWT_ALGORITHM = "RS256"
        mock_settings.JWT_PRIVATE_KEY_PATH = None

        with pytest.raises(RuntimeError, match="JWT_PRIVATE_KEY_PATH must be set"):
            JWTUtils._get_sign_key()

    @patch("app.utils.jwt.settings")
    def test_get_sign_key_unsupported_algorithm(self, mock_settings):
        """Test _get_sign_key with unsupported algorithm."""
        mock_settings.JWT_ALGORITHM = "ES256"

        with pytest.raises(RuntimeError, match="Unsupported JWT_ALGORITHM"):
            JWTUtils._get_sign_key()

    @patch("app.utils.jwt.settings")
    def test_get_verify_key_hs256_with_keys(self, mock_settings):
        """Test _get_verify_key with HS256 and JWT_KEYS."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_settings.ACTIVE_JWT_KID = "kid1"

        result = JWTUtils._get_verify_key()
        assert result == "secret1"

    @patch("app.utils.jwt.settings")
    def test_get_verify_key_hs256_fallback_to_first_key(self, mock_settings):
        """Test _get_verify_key falls back to first key when active KID not found."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_settings.ACTIVE_JWT_KID = "missing_kid"

        result = JWTUtils._get_verify_key()
        assert result == "secret1"  # First key in dict

    @patch("app.utils.jwt.settings")
    def test_get_verify_key_hs256_fallback_to_signing_key(self, mock_settings):
        """Test _get_verify_key falls back to signing key when no JWT_KEYS."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = None
        mock_settings.JWT_SECRET_KEY = "fallback_secret"

        result = JWTUtils._get_verify_key()
        assert result == "fallback_secret"

    @patch("app.utils.jwt.settings")
    @patch("builtins.open", new_callable=mock_open, read_data="public_key_content")
    def test_get_verify_key_rs256(self, mock_file, mock_settings):
        """Test _get_verify_key with RS256 algorithm."""
        mock_settings.JWT_ALGORITHM = "RS256"
        mock_settings.JWT_PUBLIC_KEY_PATH = "/path/to/public.key"

        result = JWTUtils._get_verify_key()
        assert result == "public_key_content"
        mock_file.assert_called_once_with("/path/to/public.key", "r", encoding="utf-8")

    @patch("app.utils.jwt.settings")
    def test_get_verify_key_rs256_missing_public_key_path(self, mock_settings):
        """Test _get_verify_key with RS256 and missing public key path."""
        mock_settings.JWT_ALGORITHM = "RS256"
        mock_settings.JWT_PUBLIC_KEY_PATH = None

        with pytest.raises(RuntimeError, match="JWT_PUBLIC_KEY_PATH must be set"):
            JWTUtils._get_verify_key()

    @patch("app.utils.jwt.settings")
    def test_get_verify_key_unsupported_algorithm(self, mock_settings):
        """Test _get_verify_key with unsupported algorithm."""
        mock_settings.JWT_ALGORITHM = "ES256"

        with pytest.raises(RuntimeError, match="Unsupported JWT_ALGORITHM"):
            JWTUtils._get_verify_key()

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.encode")
    def test_create_access_token_success(self, mock_encode, mock_settings):
        """Test successful access token creation."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_encode.return_value = "encoded_token"

        result = JWTUtils.create_access_token("user123")

        assert result == "encoded_token"
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args
        assert call_args[0][1] == "secret1"  # signing key
        assert call_args[1]["algorithm"] == "HS256"
        assert call_args[1]["headers"] == {"kid": "kid1"}

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.encode")
    def test_create_access_token_with_additional_claims(
        self, mock_encode, mock_settings
    ):
        """Test access token creation with additional claims."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_encode.return_value = "encoded_token"

        additional_claims = {"role": "admin", "permissions": ["read", "write"]}
        result = JWTUtils.create_access_token(
            "user123", additional_claims=additional_claims
        )

        assert result == "encoded_token"
        call_args = mock_encode.call_args
        payload = call_args[0][0]
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.encode")
    def test_create_access_token_with_custom_expiry(self, mock_encode, mock_settings):
        """Test access token creation with custom expiry."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_encode.return_value = "encoded_token"

        custom_expiry = timedelta(hours=2)
        result = JWTUtils.create_access_token("user123", expires_delta=custom_expiry)

        assert result == "encoded_token"
        call_args = mock_encode.call_args
        payload = call_args[0][0]
        # Verify expiry is set correctly (rough check)
        assert "exp" in payload
        assert "iat" in payload

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.encode")
    def test_create_access_token_retry_with_alt_key_representation(
        self, mock_encode, mock_settings
    ):
        """Test access token creation with retry on encoding error."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        # First call fails, second succeeds
        mock_encode.side_effect = [JWTError("encoding error"), "encoded_token"]

        result = JWTUtils.create_access_token("user123")

        assert result == "encoded_token"
        assert mock_encode.call_count == 2

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.encode")
    def test_create_refresh_token_success(self, mock_encode, mock_settings):
        """Test successful refresh token creation."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
        mock_encode.return_value = "refresh_token"

        result = JWTUtils.create_refresh_token("user123")

        assert result == "refresh_token"
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args
        payload = call_args[0][0]
        assert payload["type"] == "refresh"
        assert payload["sub"] == "user123"

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_success(self, mock_get_header, mock_decode, mock_settings):
        """Test successful token decoding."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"

        expected_payload = {"sub": "user123", "type": "access"}
        mock_decode.return_value = expected_payload
        mock_get_header.return_value = {"kid": "kid1"}

        # Use a minimal valid JWT string (three dot-separated segments)
        result = JWTUtils.decode_token("a.b.c")

        assert result == expected_payload
        mock_decode.assert_called_once()

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_expired_signature(
        self, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding with expired signature."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"

        mock_decode.side_effect = ExpiredSignatureError("Token has expired")
        mock_get_header.return_value = {"kid": "kid1"}

        with pytest.raises(ExpiredSignatureError):
            JWTUtils.decode_token("a.b.c")

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_jwt_error(self, mock_get_header, mock_decode, mock_settings):
        """Test token decoding with JWT error."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"

        mock_decode.side_effect = JWTError("Invalid token")
        mock_get_header.return_value = {"kid": "kid1"}

        with pytest.raises(JWTError):
            JWTUtils.decode_token("a.b.c")

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_with_retired_keys(
        self, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding with retired keys."""
        import app.utils.jwt as jwt_module

        jwt_module._RETIRED_KEYS.clear()

        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1", "kid2": "secret2"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600

        # Add a retired key
        jwt_module._RETIRED_KEYS["kid2"] = datetime.now(timezone.utc) + timedelta(
            hours=1
        )

        # Token has kid2 (retired key), so decode should succeed with secret2
        mock_decode.return_value = {"sub": "user123"}
        mock_get_header.return_value = {"kid": "kid2"}

        result = JWTUtils.decode_token("a.b.c")

        assert result == {"sub": "user123"}
        assert mock_decode.call_count == 1
        # Verify it was called with the correct key for kid2
        mock_decode.assert_called_once_with(
            "a.b.c", "secret2", algorithms=["HS256"], options=ANY
        )

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_all_keys_fail(
        self, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding when all keys fail."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"

        mock_decode.side_effect = JWTError("Invalid token")
        mock_get_header.return_value = {"kid": "kid1"}

        with pytest.raises(JWTError):
            JWTUtils.decode_token("a.b.c")

    def test_load_key_success(self):
        """Test successful key loading from file."""
        with patch("builtins.open", mock_open(read_data="key_content")):
            result = JWTUtils._load_key("/path/to/key")
            assert result == "key_content"

    def test_to_text_with_string(self):
        """Test _to_text with string input."""
        result = _to_text("test_string")
        assert result == "test_string"

    def test_to_text_with_bytes(self):
        """Test _to_text with bytes input."""
        result = _to_text(b"test_bytes")
        assert result == "test_bytes"

    def test_now_utc(self):
        """Test _now_utc returns UTC datetime."""
        result = _now_utc()
        assert result.tzinfo == timezone.utc


class TestRotateSigningKey:
    """Test key rotation functionality."""

    def setup_method(self):
        """Clear retired keys before each test."""
        _RETIRED_KEYS.clear()

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.audit")
    def test_rotate_signing_key_new_key(self, mock_audit, mock_settings):
        """Test rotating to a new signing key."""
        mock_settings.JWT_KEYS = {"old_kid": "old_secret"}
        mock_settings.ACTIVE_JWT_KID = "old_kid"
        mock_settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600

        rotate_signing_key("new_kid", "new_secret")

        assert mock_settings.JWT_KEYS["new_kid"] == "new_secret"
        assert mock_settings.ACTIVE_JWT_KID == "new_kid"
        assert "old_kid" in _RETIRED_KEYS
        mock_audit.assert_called_once()

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.audit")
    def test_rotate_signing_key_same_key(self, mock_audit, mock_settings):
        """Test rotating to the same key (no-op)."""
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600

        rotate_signing_key("kid1", "secret1")

        assert mock_settings.ACTIVE_JWT_KID == "kid1"
        assert "kid1" not in _RETIRED_KEYS
        mock_audit.assert_called_once()

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.audit")
    def test_rotate_signing_key_no_existing_keys(self, mock_audit, mock_settings):
        """Test rotating when no existing keys."""
        mock_settings.JWT_KEYS = None
        mock_settings.ACTIVE_JWT_KID = None
        mock_settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600

        rotate_signing_key("new_kid", "new_secret")

        assert mock_settings.JWT_KEYS["new_kid"] == "new_secret"
        assert mock_settings.ACTIVE_JWT_KID == "new_kid"
        assert len(_RETIRED_KEYS) == 0
        mock_audit.assert_called_once()

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.audit")
    def test_rotate_signing_key_old_key_not_in_keys(self, mock_audit, mock_settings):
        """Test rotating when old key is not in JWT_KEYS."""
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "missing_kid"
        mock_settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600

        rotate_signing_key("new_kid", "new_secret")

        assert mock_settings.JWT_KEYS["new_kid"] == "new_secret"
        assert mock_settings.ACTIVE_JWT_KID == "new_kid"
        assert "missing_kid" not in _RETIRED_KEYS
        mock_audit.assert_called_once()
