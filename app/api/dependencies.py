from __future__ import annotations

import uuid
from typing import AsyncGenerator

from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from redis import Redis

from app.core.config import Configuration
from app.core.security.roles import ROLE_PERMISSIONS_MAP, UserRole
from app.models.user import User
from app.utils.rate_limiter import login_rate_limiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class AuthDeps:
    """Rate-limit, OAuth2 scheme, and *current-user* helper."""

    # Standard OAuth2 bearer scheme – requires "Authorization: Bearer <token>" header.
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

    def __init__(self):
        """Initialize with configuration service."""
        self.config = Configuration()

    async def rate_limit_auth_token(  # type: ignore[valid-type]
        self, request: Request
    ) -> None:
        """Throttle excessive login attempts per client IP (in-memory)."""

        identifier = request.client.host or "unknown"

        if not login_rate_limiter.allow(identifier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts, please try again later.",
                headers={
                    "Retry-After": str(self.config.AUTH_RATE_LIMIT_WINDOW_SECONDS)
                },
            )


# Instantiate auth deps singleton
auth_deps = AuthDeps()


def get_user_id_from_request(request: Request) -> uuid.UUID:
    """
    Get user_id from request state (set by JWTAuthMiddleware).
    Raises HTTPException if user is not authenticated.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_user_from_request(request: Request) -> User:
    """
    Get user from database using user_id from request state (set by JWTAuthMiddleware).
    Attaches roles and attributes from token payload to the user object.
    Raises HTTPException if user is not authenticated or not found.
    """
    # Get user_id from request state
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get token payload for roles and attributes
    payload = getattr(request.state, "token_payload", None)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get database service from DI container (local import to avoid circular import)
    from app.main import di_container

    database = di_container.get_core("database")

    async with database.get_session() as db:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Attach roles and attributes from token payload to the user object
        user._current_roles = payload.get("roles", [])  # type: ignore[attr-defined]
        user._current_attributes = payload.get(  # type: ignore[attr-defined]
            "attributes", {}
        )

        return user


__all__ = [
    "auth_deps",
    "get_redis",
    "get_user_id_from_request",
    "get_user_from_request",
]


async def get_redis() -> AsyncGenerator["Redis", None]:  # type: ignore[name-defined]
    """Provide a managed Redis client for request scope."""

    config = Configuration()
    client: Redis = Redis.from_url(config.redis_url)
    try:
        yield client
    finally:
        try:
            await client.close()
        except Exception:  # noqa: BLE001 – ignore shutdown errors
            pass  # nosec B110 – best-effort shutdown cleanup


# ---------------------------------------------------------------------------
# Group helpers into a convenient class while preserving existing API
# ---------------------------------------------------------------------------


class AuthorizationDeps:  # noqa: D101
    """FastAPI dependencies for role-based and attribute-based access control."""

    def __init__(self):
        pass

    def _ensure_list(self, value):
        """Convert single values to lists for consistent processing."""
        return value if isinstance(value, list) else [value]

    def _match_attribute(self, value, requirement):
        """Check if a user attribute value matches a requirement."""
        if isinstance(requirement, dict):
            op = requirement.get("op", "eq")
            req_value = requirement.get("value")

            if op == "eq":
                return value == req_value
            elif op == "neq":
                return value != req_value
            elif op == "gt":
                return value > req_value
            elif op == "gte":
                return value >= req_value
            elif op == "lt":
                return value < req_value
            elif op == "lte":
                return value <= req_value
            elif op == "in":
                return value in self._ensure_list(req_value)
            elif op == "not_in":
                return value not in self._ensure_list(req_value)
            else:
                return False
        else:
            # Simple equality check
            return value == requirement

    def _expand_permissions(self, user_roles: list[str]):
        """Get all permissions for given roles."""
        permissions = set()
        for role in user_roles:
            role_enum = UserRole(role) if role in [r.value for r in UserRole] else None
            if role_enum and role_enum in ROLE_PERMISSIONS_MAP:
                permissions.update(ROLE_PERMISSIONS_MAP[role_enum])
        return permissions

    def has_permission(
        self, user_roles: list[str], required_permission: str
    ) -> bool:  # pragma: no cover
        """Check if user has required permission through their roles."""
        user_permissions = self._expand_permissions(user_roles)
        return required_permission in user_permissions

    def require_roles(self, required_roles: list[str]):  # noqa: D401
        """Create a dependency that enforces role requirements (OR logic)."""

        def dependency(request: Request):
            # Get token payload from request state (set by middleware)
            payload = getattr(request.state, "token_payload", None)
            if payload is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Use JWT claims for role checking
            user_roles = payload.get("roles", [UserRole.INDIVIDUAL_INVESTOR.value])

            # Check if user has any of the required roles
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Access denied. Required roles: %s. Your roles: %s"
                        % (required_roles, user_roles)
                    ),
                )
            return request

        return dependency

    def require_attributes(self, requirements: dict[str, any]):  # noqa: D401
        """Create a dependency that enforces attribute requirements."""

        def dependency(request: Request):
            # Get token payload from request state (set by middleware)
            payload = getattr(request.state, "token_payload", None)
            if payload is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Use JWT claims for attribute checking
            user_attributes = payload.get("attributes", {})

            for attr_name, requirement in requirements.items():
                user_value = user_attributes.get(attr_name)
                if user_value is None or not self._match_attribute(
                    user_value, requirement
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            "Access denied. Attribute '%s' "
                            "requirement not met." % attr_name
                        ),
                    )
            return request

        return dependency

    def require_permission(self, required_permission: str):  # noqa: D401
        """Create a dependency that enforces permission requirements."""

        def dependency(request: Request):
            # Get token payload from request state (set by middleware)
            payload = getattr(request.state, "token_payload", None)
            if payload is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Use JWT claims for permission checking
            user_roles = payload.get("roles", [UserRole.INDIVIDUAL_INVESTOR.value])

            if not self.has_permission(user_roles, required_permission):
                user_permissions = self._expand_permissions(user_roles)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Access denied. Required permission: %s. Your permissions: %s"
                        % (required_permission, list(user_permissions))
                    ),
                )
            return request

        return dependency


authz_deps = AuthorizationDeps()

require_roles = authz_deps.require_roles
require_attributes = authz_deps.require_attributes
require_permission = authz_deps.require_permission
has_permission = authz_deps.has_permission

# Export symbols
__all__.extend(
    [
        "require_roles",
        "require_attributes",
        "require_permission",
        "has_permission",
    ]
)
