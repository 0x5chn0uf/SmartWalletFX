"""Unit tests for EmailVerificationUsecase."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import BackgroundTasks, HTTPException
from jose import jwt as jose_jwt

from app.core.security.roles import UserRole
from app.domain.schemas.auth_token import TokenResponse
from app.models.email_verification import EmailVerification
from app.models.user import User
from app.usecase.email_verification_usecase import EmailVerificationUsecase
from app.utils.rate_limiter import InMemoryRateLimiter


class TestEmailVerificationUsecase:
    """Test EmailVerificationUsecase class."""

    def test_init(self, email_verification_usecase_with_di):
        """Test EmailVerificationUsecase initialization."""
        usecase = email_verification_usecase_with_di

        assert usecase._EmailVerificationUsecase__ev_repo is not None
        assert usecase._EmailVerificationUsecase__user_repo is not None
        assert usecase._EmailVerificationUsecase__rt_repo is not None
        assert usecase._EmailVerificationUsecase__email_service is not None
        assert usecase._EmailVerificationUsecase__jwt_utils is not None
        assert usecase._EmailVerificationUsecase__config_service is not None
        assert usecase._EmailVerificationUsecase__audit is not None

    @pytest.mark.asyncio
    async def test_verify_email_success(self, email_verification_usecase_with_di):
        """Test successful email verification."""
        usecase = email_verification_usecase_with_di
        token = "valid_token_123"
        user_id = uuid.uuid4()
        jti = "jti_123"

        # Mock token object
        token_obj = Mock()
        token_obj.user_id = user_id

        # Mock user
        user = Mock()
        user.id = user_id
        user.email_verified = False
        user.roles = [UserRole.INDIVIDUAL_INVESTOR.value]
        user.attributes = {"test": "value"}

        # Mock responses
        usecase._EmailVerificationUsecase__ev_repo.get_valid = AsyncMock(
            return_value=token_obj
        )
        usecase._EmailVerificationUsecase__user_repo.get_by_id = AsyncMock(
            return_value=user
        )
        usecase._EmailVerificationUsecase__user_repo.save = AsyncMock(return_value=user)
        usecase._EmailVerificationUsecase__ev_repo.mark_used = AsyncMock()
        usecase._EmailVerificationUsecase__rt_repo.create_from_jti = AsyncMock()

        # Mock JWT utils
        usecase._EmailVerificationUsecase__jwt_utils.create_access_token = Mock(
            return_value="access_token"
        )
        usecase._EmailVerificationUsecase__jwt_utils.create_refresh_token = Mock(
            return_value="refresh_token"
        )

        # Mock config
        usecase._EmailVerificationUsecase__config_service.REFRESH_TOKEN_EXPIRE_DAYS = 30
        usecase._EmailVerificationUsecase__config_service.ACCESS_TOKEN_EXPIRE_MINUTES = (
            15
        )

        # Mock jose_jwt
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                jose_jwt, "get_unverified_claims", Mock(return_value={"jti": jti})
            )

            # Execute
            result = await usecase.verify_email(token)

            # Verify result
            assert isinstance(result, TokenResponse)
            assert result.access_token == "access_token"
            assert result.refresh_token == "refresh_token"
            assert result.token_type == "bearer"
            assert result.expires_in == 15 * 60

            # Verify user was marked as verified
            assert user.email_verified is True

            # Verify method calls
            usecase._EmailVerificationUsecase__ev_repo.get_valid.assert_called_once_with(
                token
            )
            usecase._EmailVerificationUsecase__user_repo.get_by_id.assert_called_once_with(
                user_id
            )
            usecase._EmailVerificationUsecase__user_repo.save.assert_called_once_with(
                user
            )
            usecase._EmailVerificationUsecase__ev_repo.mark_used.assert_called_once_with(
                token_obj
            )
            usecase._EmailVerificationUsecase__rt_repo.create_from_jti.assert_called_once()

            # Verify JWT creation
            usecase._EmailVerificationUsecase__jwt_utils.create_access_token.assert_called_once()
            usecase._EmailVerificationUsecase__jwt_utils.create_refresh_token.assert_called_once_with(
                str(user_id)
            )

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, email_verification_usecase_with_di):
        """Test email verification with invalid token."""
        usecase = email_verification_usecase_with_di
        token = "invalid_token"

        # Mock invalid token
        usecase._EmailVerificationUsecase__ev_repo.get_valid = AsyncMock(
            return_value=None
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.verify_email(token)

        assert exc_info.value.status_code == 400
        assert "Invalid or expired token" in str(exc_info.value.detail)

        # Verify audit was called
        usecase._EmailVerificationUsecase__audit.warning.assert_called_once_with(
            "invalid_email_verification_token"
        )

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found(
        self, email_verification_usecase_with_di
    ):
        """Test email verification when user is not found."""
        usecase = email_verification_usecase_with_di
        token = "valid_token_123"
        user_id = uuid.uuid4()

        # Mock token object
        token_obj = Mock()
        token_obj.user_id = user_id

        # Mock responses
        usecase._EmailVerificationUsecase__ev_repo.get_valid = AsyncMock(
            return_value=token_obj
        )
        usecase._EmailVerificationUsecase__user_repo.get_by_id = AsyncMock(
            return_value=None
        )

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.verify_email(token)

        assert exc_info.value.status_code == 400
        assert "User not found" in str(exc_info.value.detail)

        # Verify audit was called with specific error
        usecase._EmailVerificationUsecase__audit.error.assert_any_call(
            "user_not_found_for_verification", user_id=str(user_id)
        )
        # Should also be called with general exception
        assert usecase._EmailVerificationUsecase__audit.error.call_count == 2

    @pytest.mark.asyncio
    async def test_verify_email_with_default_role(
        self, email_verification_usecase_with_di
    ):
        """Test email verification with default role when user has no roles."""
        usecase = email_verification_usecase_with_di
        token = "valid_token_123"
        user_id = uuid.uuid4()
        jti = "jti_123"

        # Mock token object
        token_obj = Mock()
        token_obj.user_id = user_id

        # Mock user with no roles
        user = Mock()
        user.id = user_id
        user.email_verified = False
        user.roles = None
        user.attributes = None

        # Mock responses
        usecase._EmailVerificationUsecase__ev_repo.get_valid = AsyncMock(
            return_value=token_obj
        )
        usecase._EmailVerificationUsecase__user_repo.get_by_id = AsyncMock(
            return_value=user
        )
        usecase._EmailVerificationUsecase__user_repo.save = AsyncMock(return_value=user)
        usecase._EmailVerificationUsecase__ev_repo.mark_used = AsyncMock()
        usecase._EmailVerificationUsecase__rt_repo.create_from_jti = AsyncMock()

        # Mock JWT utils
        usecase._EmailVerificationUsecase__jwt_utils.create_access_token = Mock(
            return_value="access_token"
        )
        usecase._EmailVerificationUsecase__jwt_utils.create_refresh_token = Mock(
            return_value="refresh_token"
        )

        # Mock config
        usecase._EmailVerificationUsecase__config_service.REFRESH_TOKEN_EXPIRE_DAYS = 30
        usecase._EmailVerificationUsecase__config_service.ACCESS_TOKEN_EXPIRE_MINUTES = (
            15
        )

        # Mock jose_jwt
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                jose_jwt, "get_unverified_claims", Mock(return_value={"jti": jti})
            )

            # Execute
            result = await usecase.verify_email(token)

            # Verify result
            assert isinstance(result, TokenResponse)

            # Verify JWT creation with default role
            call_args = (
                usecase._EmailVerificationUsecase__jwt_utils.create_access_token.call_args
            )
            additional_claims = call_args[1]["additional_claims"]
            assert additional_claims["roles"] == [UserRole.INDIVIDUAL_INVESTOR.value]
            assert additional_claims["attributes"] == {}

    @pytest.mark.asyncio
    async def test_verify_email_exception_handling(
        self, email_verification_usecase_with_di
    ):
        """Test email verification exception handling."""
        usecase = email_verification_usecase_with_di
        token = "valid_token_123"

        # Mock exception
        usecase._EmailVerificationUsecase__ev_repo.get_valid = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.verify_email(token)

        # Verify audit was called
        usecase._EmailVerificationUsecase__audit.error.assert_called_with(
            "email_verification_failed", error="Database error"
        )

    @pytest.mark.asyncio
    async def test_resend_verification_success(
        self, email_verification_usecase_with_di
    ):
        """Test successful resend verification."""
        usecase = email_verification_usecase_with_di
        email = "test@example.com"
        background_tasks = Mock(spec=BackgroundTasks)
        rate_limiter = Mock(spec=InMemoryRateLimiter)
        user_id = uuid.uuid4()

        # Mock rate limiter
        rate_limiter.allow.return_value = True

        # Mock user
        user = Mock()
        user.id = user_id
        user.email = email
        user.email_verified = False

        # Mock responses
        usecase._EmailVerificationUsecase__user_repo.get_by_email = AsyncMock(
            return_value=user
        )
        usecase._EmailVerificationUsecase__ev_repo.create = AsyncMock()

        # Mock config
        usecase._EmailVerificationUsecase__config_service.FRONTEND_BASE_URL = (
            "https://example.com/"
        )

        # Mock token generation
        with pytest.MonkeyPatch.context() as m:
            expires_at = datetime.utcnow() + timedelta(hours=24)
            m.setattr(
                "app.usecase.email_verification_usecase.generate_verification_token",
                Mock(return_value=("token_123", "hash_123", expires_at)),
            )

            # Execute
            await usecase.resend_verification(email, background_tasks, rate_limiter)

            # Verify method calls
            rate_limiter.allow.assert_called_once_with(email.lower())
            usecase._EmailVerificationUsecase__user_repo.get_by_email.assert_called_once_with(
                email
            )
            usecase._EmailVerificationUsecase__ev_repo.create.assert_called_once_with(
                "token_123", user_id, expires_at
            )

            # Verify background task was added
            background_tasks.add_task.assert_called_once()

            # Verify audit was called
            usecase._EmailVerificationUsecase__audit.info.assert_called_with(
                "verification_email_resent", user_id=str(user_id)
            )

    @pytest.mark.asyncio
    async def test_resend_verification_rate_limited(
        self, email_verification_usecase_with_di
    ):
        """Test resend verification when rate limited."""
        usecase = email_verification_usecase_with_di
        email = "test@example.com"
        background_tasks = Mock(spec=BackgroundTasks)
        rate_limiter = Mock(spec=InMemoryRateLimiter)

        # Mock rate limiter to deny
        rate_limiter.allow.return_value = False

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await usecase.resend_verification(email, background_tasks, rate_limiter)

        assert exc_info.value.status_code == 429
        assert "Too many requests" in str(exc_info.value.detail)

        # Verify audit was called with specific error
        usecase._EmailVerificationUsecase__audit.error.assert_any_call(
            "email_verification_rate_limited", email=email
        )
        # Should also be called with general exception
        assert usecase._EmailVerificationUsecase__audit.error.call_count == 2

    @pytest.mark.asyncio
    async def test_resend_verification_user_not_found(
        self, email_verification_usecase_with_di
    ):
        """Test resend verification when user is not found."""
        usecase = email_verification_usecase_with_di
        email = "test@example.com"
        background_tasks = Mock(spec=BackgroundTasks)
        rate_limiter = Mock(spec=InMemoryRateLimiter)

        # Mock rate limiter
        rate_limiter.allow.return_value = True

        # Mock user not found
        usecase._EmailVerificationUsecase__user_repo.get_by_email = AsyncMock(
            return_value=None
        )

        # Execute - should succeed silently
        await usecase.resend_verification(email, background_tasks, rate_limiter)

        # Verify audit was called
        usecase._EmailVerificationUsecase__audit.warning.assert_called_once_with(
            "verification_email_resend_unknown_or_verified", email=email
        )

        # Verify no background task was added
        background_tasks.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_resend_verification_user_already_verified(
        self, email_verification_usecase_with_di
    ):
        """Test resend verification when user is already verified."""
        usecase = email_verification_usecase_with_di
        email = "test@example.com"
        background_tasks = Mock(spec=BackgroundTasks)
        rate_limiter = Mock(spec=InMemoryRateLimiter)

        # Mock rate limiter
        rate_limiter.allow.return_value = True

        # Mock verified user
        user = Mock()
        user.email_verified = True
        usecase._EmailVerificationUsecase__user_repo.get_by_email = AsyncMock(
            return_value=user
        )

        # Execute - should succeed silently
        await usecase.resend_verification(email, background_tasks, rate_limiter)

        # Verify audit was called
        usecase._EmailVerificationUsecase__audit.warning.assert_called_once_with(
            "verification_email_resend_unknown_or_verified", email=email
        )

        # Verify no background task was added
        background_tasks.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_resend_verification_exception_handling(
        self, email_verification_usecase_with_di
    ):
        """Test resend verification exception handling."""
        usecase = email_verification_usecase_with_di
        email = "test@example.com"
        background_tasks = Mock(spec=BackgroundTasks)
        rate_limiter = Mock(spec=InMemoryRateLimiter)

        # Mock rate limiter
        rate_limiter.allow.return_value = True

        # Mock exception
        usecase._EmailVerificationUsecase__user_repo.get_by_email = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Execute and verify exception
        with pytest.raises(Exception, match="Database error"):
            await usecase.resend_verification(email, background_tasks, rate_limiter)

        # Verify audit was called
        usecase._EmailVerificationUsecase__audit.error.assert_called_with(
            "resend_verification_failed", email=email, error="Database error"
        )

    @pytest.mark.asyncio
    async def test_resend_verification_frontend_url_stripping(
        self, email_verification_usecase_with_di
    ):
        """Test resend verification strips trailing slash from frontend URL."""
        usecase = email_verification_usecase_with_di
        email = "test@example.com"
        background_tasks = Mock(spec=BackgroundTasks)
        rate_limiter = Mock(spec=InMemoryRateLimiter)
        user_id = uuid.uuid4()

        # Mock rate limiter
        rate_limiter.allow.return_value = True

        # Mock user
        user = Mock()
        user.id = user_id
        user.email = email
        user.email_verified = False

        # Mock responses
        usecase._EmailVerificationUsecase__user_repo.get_by_email = AsyncMock(
            return_value=user
        )
        usecase._EmailVerificationUsecase__ev_repo.create = AsyncMock()

        # Mock config with trailing slash
        usecase._EmailVerificationUsecase__config_service.FRONTEND_BASE_URL = (
            "https://example.com/"
        )

        # Mock token generation
        with pytest.MonkeyPatch.context() as m:
            expires_at = datetime.utcnow() + timedelta(hours=24)
            m.setattr(
                "app.usecase.email_verification_usecase.generate_verification_token",
                Mock(return_value=("token_123", "hash_123", expires_at)),
            )

            # Execute
            await usecase.resend_verification(email, background_tasks, rate_limiter)

            # Verify background task was added with correct URL
            background_tasks.add_task.assert_called_once()
            call_args = background_tasks.add_task.call_args
            verify_link = call_args[0][2]  # third argument is the verify_link
            assert verify_link == "https://example.com/verify-email?token=token_123"
