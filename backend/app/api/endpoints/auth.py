from __future__ import annotations

"""Authentication endpoints"""

import time

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

import app.api.dependencies as deps_mod
from app.core.database import get_db
from app.domain.errors import InactiveUserError, InvalidCredentialsError
from app.schemas.auth_token import TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    AuthService,
    DuplicateError,
    WeakPasswordError,
)
from app.utils.logging import audit

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    summary="Register a new user",
)
async def register_user(
    request: Request,
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:  # type: ignore[valid-type]
    """Create a new user account.

    Returns the newly-created user object excluding sensitive fields.
    """
    start_time = time.time()
    client_ip = request.client.host or "unknown"

    logger.info(
        "User registration started",
        username=payload.username,
        email=payload.email,
        client_ip=client_ip,
    )

    service = AuthService(db)
    try:
        user = await service.register(payload)
        duration = int((time.time() - start_time) * 1000)

        logger.info(
            "User registration completed successfully",
            user_id=user.id,
            username=user.username,
            email=user.email,
            duration_ms=duration,
        )

        audit(
            "user_registration_success",
            user_id=user.id,
            username=user.username,
            email=user.email,
            client_ip=client_ip,
        )

        return user
    except DuplicateError as dup:
        duration = int((time.time() - start_time) * 1000)
        logger.warning(
            "User registration failed - duplicate field",
            username=payload.username,
            email=payload.email,
            duplicate_field=dup.field,
            duration_ms=duration,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{dup.field} already exists",
        ) from dup
    except WeakPasswordError:
        duration = int((time.time() - start_time) * 1000)
        logger.warning(
            "User registration failed - weak password",
            username=payload.username,
            email=payload.email,
            duration_ms=duration,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet strength requirements",
        )
    except Exception as exc:
        duration = int((time.time() - start_time) * 1000)
        logger.error(
            "User registration failed with unexpected error",
            username=payload.username,
            email=payload.email,
            duration_ms=duration,
            error=str(exc),
            exc_info=True,
        )
        raise


@router.post(
    "/token",
    summary="Obtain JWT bearer tokens",
    response_model=TokenResponse,
)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:  # type: ignore[valid-type]
    """OAuth2 Password grant – return access & refresh tokens."""
    start_time = time.time()
    identifier = request.client.host or "unknown"
    limiter = deps_mod.login_rate_limiter

    logger.info(
        "User login attempt started", username=form_data.username, client_ip=identifier
    )

    service = AuthService(db)
    try:
        tokens = await service.authenticate(form_data.username, form_data.password)
        # Successful login → reset any accumulated failures for this IP
        limiter.reset(identifier)

        duration = int((time.time() - start_time) * 1000)
        logger.info(
            "User login successful",
            username=form_data.username,
            client_ip=identifier,
            duration_ms=duration,
        )

        audit("user_login_success", username=form_data.username, client_ip=identifier)

        return tokens
    except InvalidCredentialsError:
        duration = int((time.time() - start_time) * 1000)
        logger.warning(
            "User login failed - invalid credentials",
            username=form_data.username,
            client_ip=identifier,
            duration_ms=duration,
        )

        audit(
            "user_login_failed_invalid_credentials",
            username=form_data.username,
            client_ip=identifier,
        )

        # Failed credentials → consume one hit and maybe block further attempts
        if not limiter.allow(identifier):
            logger.warning(
                "Login rate limit exceeded",
                username=form_data.username,
                client_ip=identifier,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts, please try again later.",
            )
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    except InactiveUserError:
        duration = int((time.time() - start_time) * 1000)
        logger.warning(
            "User login failed - inactive account",
            username=form_data.username,
            client_ip=identifier,
            duration_ms=duration,
        )

        audit(
            "user_login_failed_inactive_account",
            username=form_data.username,
            client_ip=identifier,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive or disabled user account",
        )
    except Exception as exc:
        duration = int((time.time() - start_time) * 1000)
        logger.error(
            "User login failed with unexpected error",
            username=form_data.username,
            client_ip=identifier,
            duration_ms=duration,
            error=str(exc),
            exc_info=True,
        )
        raise


class _RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid JWT refresh token")


@router.post(
    "/refresh",
    summary="Refresh access token using refresh JWT",
    response_model=TokenResponse,
)
async def refresh_access_token(
    request: Request,
    payload: _RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:  # type: ignore[valid-type]
    """Exchange *refresh_token* for a new access token.

    The new access token contains the latest roles/attributes claims.
    """
    start_time = time.time()
    client_ip = request.client.host or "unknown"

    logger.info("Token refresh attempt started", client_ip=client_ip)

    service = AuthService(db)
    try:
        tokens = await service.refresh(payload.refresh_token)

        duration = int((time.time() - start_time) * 1000)
        logger.info(
            "Token refresh successful", client_ip=client_ip, duration_ms=duration
        )

        return tokens
    except Exception as exc:  # noqa: BLE001
        duration = int((time.time() - start_time) * 1000)
        logger.warning(
            "Token refresh failed",
            client_ip=client_ip,
            duration_ms=duration,
            error=str(exc),
        )

        audit(
            "token_refresh_failed", client_ip=client_ip, error_type=type(exc).__name__
        )

        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
