"""Authentication endpoints"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from starlette.status import HTTP_401_UNAUTHORIZED

import app.api.dependencies as deps_mod
from app.domain.errors import (
    InactiveUserError,
    InvalidCredentialsError,
    UnverifiedEmailError,
)
from app.domain.schemas.auth_token import TokenResponse
from app.domain.schemas.user import UserCreate, UserRead, WeakPasswordError
from app.services.auth_service import AuthService, DuplicateError
from app.utils.logging import Audit


class _RefreshRequest(BaseModel):
    refresh_token: str | None = Field(None, description="Valid JWT refresh token")


class Auth:
    """Authentication endpoint using singleton pattern with dependency injection."""

    ep = APIRouter(prefix="/auth", tags=["auth"])
    __auth_service: AuthService

    def __init__(self, auth_service: AuthService):
        """Initialize with injected dependencies."""
        Auth.__auth_service = auth_service

    @staticmethod
    @ep.post(
        "/register",
        status_code=status.HTTP_201_CREATED,
        response_model=UserRead,
        summary="Register a new user",
    )
    async def register_user(
        request: Request,
        payload: UserCreate,
        background_tasks: BackgroundTasks,
    ) -> UserRead:
        """Create a new user account."""
        client_ip = request.client.host or "unknown"

        Audit.info(
            "User registration started",
            username=payload.username,
            email=payload.email,
            client_ip=client_ip,
        )

        try:
            user = await Auth.__auth_service.register(
                payload, background_tasks=background_tasks
            )

            Audit.info(
                "User registration completed successfully",
                user_id=user.id,
                username=user.username,
                email=user.email,
            )

            return user
        except DuplicateError as dup:
            Audit.error(
                "User registration failed - duplicate field",
                username=payload.username,
                email=payload.email,
                duplicate_field=dup.field,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{dup.field} already exists",
            ) from dup
        except WeakPasswordError:
            Audit.warning(
                "User registration failed - weak password",
                username=payload.username,
                email=payload.email,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet strength requirements",
            )
        except Exception as exc:
            Audit.error(
                "User registration failed with unexpected error",
                username=payload.username,
                email=payload.email,
                error=str(exc),
                exc_info=True,
            )
            raise

    @staticmethod
    @ep.post(
        "/token",
        summary="Obtain JWT bearer tokens",
        response_model=TokenResponse,
    )
    async def login_for_access_token(
        request: Request,
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
    ) -> TokenResponse:
        """OAuth2 Password grant – return access & refresh tokens."""
        identifier = request.client.host or "unknown"
        limiter = deps_mod.login_rate_limiter

        Audit.info(
            "User login attempt started",
            username=form_data.username,
            client_ip=identifier,
        )

        try:
            tokens = await Auth.__auth_service.authenticate(
                form_data.username, form_data.password
            )
            # Successful login → reset any accumulated failures for this IP
            limiter.reset(identifier)

            Audit.info(
                "User login successful",
                username=form_data.username,
                client_ip=identifier,
            )

            response.set_cookie(
                "access_token",
                tokens.access_token,
                httponly=True,
                samesite="lax",
            )
            response.set_cookie(
                "refresh_token",
                tokens.refresh_token,
                httponly=True,
                samesite="lax",
                path="/auth/refresh",
            )

            return tokens

        except InvalidCredentialsError:
            Audit.warning(
                "User login failed - invalid credentials",
                username=form_data.username,
                client_ip=identifier,
            )

            # Failed credentials → consume one hit and maybe block further attempts
            if not limiter.allow(identifier):
                Audit.warning(
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
            Audit.warning(
                "User login failed - inactive account",
                username=form_data.username,
                client_ip=identifier,
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive or disabled user account",
            )
        except UnverifiedEmailError:
            Audit.warning(
                "User login failed - email unverified",
                username=form_data.username,
                client_ip=identifier,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email address not verified",
            )
        except Exception as exc:
            Audit.error(
                "User login failed with unexpected error",
                username=form_data.username,
                client_ip=identifier,
                error=str(exc),
                exc_info=True,
            )
            raise

    @staticmethod
    @ep.post(
        "/refresh",
        summary="Refresh access token using refresh JWT",
        response_model=TokenResponse,
    )
    async def refresh_access_token(
        request: Request,
        response: Response,
        payload: _RefreshRequest | None = None,
    ) -> TokenResponse | Response:
        """Refresh access token using refresh JWT."""
        client_ip = request.client.host or "unknown"

        # Extract refresh token from payload, cookie, or Authorization header
        refresh_token = None
        if payload and payload.refresh_token:
            refresh_token = payload.refresh_token
        elif "refresh_token" in request.cookies:
            refresh_token = request.cookies["refresh_token"]
        elif "authorization" in request.headers:
            auth_header = request.headers["authorization"]
            if auth_header.startswith("Bearer "):
                refresh_token = auth_header[7:]

        if not refresh_token:
            Audit.warning(
                "Token refresh failed - no refresh token", client_ip=client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not provided",
            )

        Audit.info("Token refresh attempt started", client_ip=client_ip)

        try:
            tokens = await Auth.__auth_service.refresh_token(refresh_token)

            Audit.info("Token refresh successful", client_ip=client_ip)

            response.set_cookie(
                "access_token",
                tokens.access_token,
                httponly=True,
                samesite="lax",
            )
            response.set_cookie(
                "refresh_token",
                tokens.refresh_token,
                httponly=True,
                samesite="lax",
                path="/auth/refresh",
            )

            return tokens

        except Exception as exc:
            Audit.error(
                "Token refresh failed",
                client_ip=client_ip,
                error=str(exc),
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

    @staticmethod
    @ep.post(
        "/logout",
        status_code=status.HTTP_200_OK,
        summary="Logout current user",
        response_class=Response,
    )
    async def logout(
        request: Request,
        response: Response,
    ) -> None:
        """Logout current user."""
        client_ip = request.client.host or "unknown"

        Audit.info("User logout started", client_ip=client_ip)

        # Clear cookies
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token", path="/auth/refresh")

        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            Audit.warning(
                "Logout failed: no refresh token provided", client_ip=client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not provided",
            )

        await Auth.__auth_service.revoke_refresh_token(refresh_token)

        Audit.info("User logout completed", client_ip=client_ip)
