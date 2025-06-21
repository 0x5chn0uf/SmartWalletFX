from __future__ import annotations

"""Authentication endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.dependencies import auth_deps
from app.core.database import get_db
from app.domain.errors import InactiveUserError, InvalidCredentialsError
from app.schemas.auth_token import TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    AuthService,
    DuplicateError,
    WeakPasswordError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = auth_deps.oauth2_scheme


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    summary="Register a new user",
)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:  # type: ignore[valid-type]
    """Create a new user account.

    Returns the newly-created user object excluding sensitive fields.
    """

    service = AuthService(db)
    try:
        user = await service.register(payload)
    except DuplicateError as dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{dup.field} already exists",
        ) from dup
    except WeakPasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet strength requirements",
        )

    return user


@router.post(
    "/token",
    summary="Obtain JWT bearer tokens",
    response_model=TokenResponse,
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(auth_deps.rate_limit_auth_token),
) -> TokenResponse:  # type: ignore[valid-type]
    """OAuth2 Password grant – return access & refresh tokens."""

    service = AuthService(db)
    try:
        tokens = await service.authenticate(form_data.username, form_data.password)
        return tokens
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive or disabled user account",
        )


# Re-export for convenience in other modules
__all__ = ["router", "oauth2_scheme", "auth_deps"]
