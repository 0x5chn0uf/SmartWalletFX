"""Comprehensive unit tests for JWT utilities."""

from datetime import datetime, timedelta, timezone
from unittest.mock import mock_open, patch

import pytest
from jose import ExpiredSignatureError, JWSError, JWTError

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
        # Verify expiry is set correctly
        assert "exp" in payload
        assert "iat" in payload

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.encode")
    def test_create_access_token_retry_with_alt_key_representation(
        self, mock_encode, mock_settings
    ):
        """Test access token creation with retry using alternate key representation."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        # First call fails, second succeeds
        mock_encode.side_effect = [JWTError("Key format error"), "encoded_token"]

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
        mock_get_header.return_value = {"kid": "kid1"}
        mock_decode.return_value = {
            "sub": "user123",
            "jti": "token123",
            "exp": 1234567890,
        }

        result = JWTUtils.decode_token("valid_token")

        assert result["sub"] == "user123"
        assert result["jti"] == "token123"
        assert result["exp"] == 1234567890

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
        mock_get_header.return_value = {"kid": "kid1"}
        mock_decode.side_effect = ExpiredSignatureError("Token has expired")

        with pytest.raises(ExpiredSignatureError, match="Token has expired"):
            JWTUtils.decode_token("expired_token")

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_jwt_error(self, mock_get_header, mock_decode, mock_settings):
        """Test token decoding with JWT error."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "kid1"}
        mock_decode.side_effect = JWTError("Invalid token")

        with pytest.raises(JWTError, match="Invalid token"):
            JWTUtils.decode_token("invalid_token")

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @patch("app.utils.jwt._now_utc")
    def test_decode_token_with_retired_keys(
        self, mock_now_utc, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding with retired keys."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600

        # Set up retired key with past expiry
        retired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        _RETIRED_KEYS["retired_kid"] = retired_time
        mock_get_header.return_value = {"kid": "retired_kid"}

        # Mock current time to be after the retired key expiry
        mock_now_utc.return_value = datetime.now(timezone.utc)

        with pytest.raises(
            ExpiredSignatureError, match="Token signed with retired key"
        ):
            JWTUtils.decode_token("token_with_retired_key")

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_with_jwk_error_and_retry(
        self, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding with JWSError and successful retry."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {
            "kid1": "secret1"
        }  # string key, so alternate is bytes
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "kid1"}

        # First call fails with JWSError, second succeeds
        def side_effect(*args, **kwargs):
            print(f"jwt.decode called with args: {args}")
            key = args[1]
            if isinstance(key, str):
                raise JWSError("Key format error")
            return {"sub": "user123", "jti": "token123", "exp": 1234567890}

        mock_decode.side_effect = side_effect

        with pytest.raises(JWSError):
            JWTUtils.decode_token("valid_token")

        assert mock_decode.call_count == 1

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_all_keys_fail(
        self, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding when all key attempts fail."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "kid1"}
        mock_decode.side_effect = JWSError("Key format error")

        with pytest.raises(JWSError, match="Key format error"):
            JWTUtils.decode_token("invalid_token")

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @patch("app.utils.jwt.jwt.encode")
    def test_decode_token_signature_verification_failure(
        self, mock_encode, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding with signature verification failure."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "kid1"}
        mock_decode.return_value = {
            "sub": "user123",
            "jti": "token123",
            "exp": 1234567890,
        }
        mock_encode.return_value = "header.payload.differentSig"

        # With the stricter integrity guard in ``JWTUtils.decode_token`` a
        # mismatched signature must raise ``JWTError``.
        with pytest.raises(JWTError, match="Signature verification failed"):
            JWTUtils.decode_token("valid_token.but.wrong.signature")

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_missing_sub_claim(
        self, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding with missing sub claim."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "kid1"}
        mock_decode.return_value = {"jti": "token123", "exp": 1234567890}  # Missing sub

        with pytest.raises(
            JWTError, match="Token payload is missing required 'sub' claim"
        ):
            JWTUtils.decode_token("token_without_sub")

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_empty_sub_claim(
        self, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding with empty sub claim."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "kid1"}
        mock_decode.return_value = {
            "sub": "",
            "jti": "token123",
            "exp": 1234567890,
        }  # Empty sub

        with pytest.raises(
            JWTError, match="Token payload is missing required 'sub' claim"
        ):
            JWTUtils.decode_token("token_with_empty_sub")

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    def test_decode_token_fallback_to_default_key(
        self, mock_get_header, mock_decode, mock_settings
    ):
        """Test token decoding falls back to default key when KID not found."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "unknown_kid"}  # KID not in JWT_KEYS
        mock_decode.return_value = {
            "sub": "user123",
            "jti": "token123",
            "exp": 1234567890,
        }

        result = JWTUtils.decode_token("valid_token")

        assert result["sub"] == "user123"

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
        """Test _now_utc returns current UTC time."""
        before = datetime.now(timezone.utc)
        result = _now_utc()
        after = datetime.now(timezone.utc)
        assert before <= result <= after


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
        """Test rotating to the same key (no retirement)."""
        mock_settings.JWT_KEYS = {"same_kid": "same_secret"}
        mock_settings.ACTIVE_JWT_KID = "same_kid"
        mock_settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600

        rotate_signing_key("same_kid", "same_secret")

        assert mock_settings.ACTIVE_JWT_KID == "same_kid"
        assert "same_kid" not in _RETIRED_KEYS
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
        mock_audit.assert_called_once()

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.audit")
    def test_rotate_signing_key_old_key_not_in_keys(self, mock_audit, mock_settings):
        """Test rotating when old key is not in JWT_KEYS."""
        mock_settings.JWT_KEYS = {"other_kid": "other_secret"}
        mock_settings.ACTIVE_JWT_KID = "missing_kid"
        mock_settings.JWT_ROTATION_GRACE_PERIOD_SECONDS = 3600

        rotate_signing_key("new_kid", "new_secret")

        assert mock_settings.JWT_KEYS["new_kid"] == "new_secret"
        assert mock_settings.ACTIVE_JWT_KID == "new_kid"
        assert "missing_kid" not in _RETIRED_KEYS
        mock_audit.assert_called_once()

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @patch("app.utils.jwt.jwt.encode")
    @patch("jose.jwk.construct")
    @patch("jose.utils.base64url_decode")
    @patch("base64.urlsafe_b64decode")
    @patch("json.loads")
    def test_decode_token_manual_verification_fallback(
        self,
        mock_json_loads,
        mock_b64decode,
        mock_base64url_decode,
        mock_jwk_construct,
        mock_encode,
        mock_get_header,
        mock_decode,
        mock_settings,
    ):
        """Test manual verification fallback when all other methods fail."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "kid1"}

        # All decode attempts fail
        mock_decode.side_effect = JWSError("Key format error")

        # Mock manual verification components
        mock_base64url_decode.return_value = b"signature"
        mock_jwk_construct.return_value.verify.return_value = True
        mock_b64decode.return_value = (
            b'{"sub":"user123","jti":"token123","exp":1234567890}'
        )
        mock_json_loads.return_value = {
            "sub": "user123",
            "jti": "token123",
            "exp": 1234567890,
        }

        with pytest.raises(JWSError):
            JWTUtils.decode_token("header.payload.signature")

        assert mock_decode.call_count == 1

    @patch("app.utils.jwt.settings")
    @patch("app.utils.jwt.jwt.decode")
    @patch("app.utils.jwt.jwt.get_unverified_header")
    @patch("jose.jwk.construct")
    @patch("jose.utils.base64url_decode")
    def test_decode_token_manual_verification_invalid_signature(
        self,
        mock_base64url_decode,
        mock_jwk_construct,
        mock_get_header,
        mock_decode,
        mock_settings,
    ):
        """Test manual verification with invalid signature."""
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_KEYS = {"kid1": "secret1"}
        mock_settings.ACTIVE_JWT_KID = "kid1"
        mock_get_header.return_value = {"kid": "kid1"}

        # All decode attempts fail
        mock_decode.side_effect = JWSError("Key format error")

        # Mock manual verification with invalid signature
        mock_base64url_decode.return_value = b"signature"
        mock_jwk_construct.return_value.verify.return_value = False

        with pytest.raises(JWSError, match="Key format error"):
            JWTUtils.decode_token("header.payload.signature")
