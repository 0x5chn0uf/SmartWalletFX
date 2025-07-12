"""Authentication endpoints."""

from __future__ import annotations

import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

import app.api.dependencies as deps_mod
from app.core.database import get_db
from app.core.services import EndpointBase, ServiceContainer
from app.domain.errors import InactiveUserError, InvalidCredentialsError
from app.schemas.auth_token import TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    AuthService,
    DuplicateError,
    WeakPasswordError,
)
from app.utils.logging import Audit


class _RefreshRequest(BaseModel):
    refresh_token: str | None = Field(None, description="Valid JWT refresh token")


class AuthView(EndpointBase):
    """Class-based auth endpoints."""

    ep = APIRouter(prefix="/auth", tags=["auth"])
    __container: ServiceContainer

    def __init__(self, container: ServiceContainer) -> None:
        super().__init__(container)
        AuthView.__container = container

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
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
        db: AsyncSession = Depends(get_db),
    ) -> UserRead:
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        Audit.info(
            "User registration started",
            username=payload.username,
            email=payload.email,
            client_ip=client_ip,
        )
        service = AuthService(db)
        try:
            user = await service.register(payload)
            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "User registration completed successfully",
                user_id=user.id,
                username=user.username,
                email=user.email,
                duration_ms=duration,
            )
            return user
        except DuplicateError as dup:
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
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
            Audit.warning(
                "User registration failed - weak password",
                username=payload.username,
                email=payload.email,
                duration_ms=duration,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet strength requirements",
            )
        except Exception as exc:  # pragma: no cover - passthrough
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
                "User registration failed with unexpected error",
                username=payload.username,
                email=payload.email,
                duration_ms=duration,
                error=str(exc),
                exc_info=True,
            )
            raise

    # ------------------------------------------------------------------
    # Login/refresh/logout
    # ------------------------------------------------------------------
    @staticmethod
    @ep.post("/token", summary="Obtain JWT bearer tokens", response_model=TokenResponse)
    async def login_for_access_token(
        request: Request,
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
    ) -> TokenResponse:
        start_time = time.time()
        identifier = request.client.host or "unknown"
        limiter = deps_mod.login_rate_limiter
        Audit.info(
            "User login attempt started",
            username=form_data.username,
            client_ip=identifier,
        )
        service = AuthService(db)
        try:
            tokens = await service.authenticate(form_data.username, form_data.password)
            limiter.reset(identifier)
            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "User login successful",
                username=form_data.username,
                client_ip=identifier,
                duration_ms=duration,
            )
            Audit.info(
                "user_login_success",
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
            duration = int((time.time() - start_time) * 1000)
            Audit.warning(
                "User login failed - invalid credentials",
                username=form_data.username,
                client_ip=identifier,
                duration_ms=duration,
            )
            Audit.info(
                "user_login_failed_invalid_credentials",
                username=form_data.username,
                client_ip=identifier,
            )
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
            duration = int((time.time() - start_time) * 1000)
            Audit.warning(
                "User login failed - inactive account",
                username=form_data.username,
                client_ip=identifier,
                duration_ms=duration,
            )
            Audit.info(
                "user_login_failed_inactive_account",
                username=form_data.username,
                client_ip=identifier,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive or disabled user account",
            )
        except Exception as exc:  # pragma: no cover - passthrough
            duration = int((time.time() - start_time) * 1000)
            Audit.error(
                "User login failed with unexpected error",
                username=form_data.username,
                client_ip=identifier,
                duration_ms=duration,
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
        db: AsyncSession = Depends(get_db),
    ) -> TokenResponse | Response:
        start_time = time.time()
        client_ip = request.client.host or "unknown"
        Audit.info("Token refresh attempt started", client_ip=client_ip)
        service = AuthService(db)
        try:
            token_str = None
            if payload and payload.refresh_token:
                token_str = payload.refresh_token
            else:
                token_str = request.cookies.get("refresh_token")
            if not token_str:
                Audit.info(
                    "Token refresh skipped – no refresh token provided",
                    client_ip=client_ip,
                )
                response.status_code = status.HTTP_204_NO_CONTENT
                return response
            tokens = await service.refresh(token_str)
            duration = int((time.time() - start_time) * 1000)
            Audit.info(
                "Token refresh successful",
                client_ip=client_ip,
                duration_ms=duration,
            )
            response.set_cookie(
                "access_token",
                tokens.access_token,
                httponly=True,
                samesite="lax",
            )
            return tokens
        except Exception as exc:  # noqa: BLE001
            duration = int((time.time() - start_time) * 1000)
            Audit.warning(
                "Token refresh failed",
                client_ip=client_ip,
                duration_ms=duration,
                error=str(exc),
            )
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
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
        db: AsyncSession = Depends(get_db),
    ) -> None:
        token = request.cookies.get("refresh_token")
        if token:
            service = AuthService(db)
            await service.revoke_refresh_token(token)
        secure = AuthView.__container.settings.ENVIRONMENT.lower() == "production"
        response.set_cookie(
            "access_token",
            "",
            max_age=0,
            path="/",
            httponly=True,
            secure=secure,
            samesite="lax",
        )
        response.set_cookie(
            "refresh_token",
            "",
            max_age=0,
            path="/auth/refresh",
            httponly=True,
            secure=secure,
            samesite="lax",
        )
        response.set_cookie(
            "oauth_state",
            "",
            max_age=0,
            path="/",
            httponly=False,
            secure=secure,
            samesite="lax",
        )
        Audit.info("User logged out")


# Factory ---------------------------------------------------------------


def get_router(container: ServiceContainer) -> APIRouter:
    AuthView(container)
    return AuthView.ep


router = get_router(ServiceContainer(load_celery=False))
