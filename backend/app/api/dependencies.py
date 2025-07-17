from __future__ import annotations

import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ConfigurationService
from app.core.database import get_db
from app.core.security.roles import ROLE_PERMISSIONS_MAP, UserRole
from app.models.user import User
from app.utils.jwks_cache import _build_redis_client
from app.utils.logging import Audit
from app.utils.rate_limiter import login_rate_limiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class AuthDeps:
    """Rate-limit, OAuth2 scheme, and *current-user* helper."""

    # Standard OAuth2 bearer scheme – requires "Authorization: Bearer <token>" header.
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

    def __init__(self):
        """Initialize with configuration service."""
        self.config_service = ConfigurationService()

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
                    "Retry-After": str(
                        self.config_service.AUTH_RATE_LIMIT_WINDOW_SECONDS
                    )
                },
            )

    async def get_current_user(
        self,
        request: Request,
        db: AsyncSession = Depends(get_db),
    ) -> User:
        """Get user from DB and attach roles/attributes from token payload."""
        audit = Audit()
        payload = getattr(request.state, "token_payload", None)

        if payload is None:
            audit.warning("Token payload not found in request state")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            pk = uuid.UUID(str(payload["sub"]))
        except (KeyError, ValueError, TypeError):
            audit.warning("Invalid subject in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid subject in token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await db.get(User, pk)
        if not user:
            audit.warning("User not found for pk from token", user_id=str(pk))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Attach roles and attributes from token payload to the user object
        user._current_roles = payload.get("roles", [])  # type: ignore[attr-defined]
        user._current_attributes = payload.get(
            "attributes", {}
        )  # type: ignore[attr-defined]

        audit.info("User loaded from token payload", user_id=str(user.id))

        return user


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


__all__ = [
    "auth_deps",
    "get_redis",
    "get_user_id_from_request",
]


async def get_redis() -> AsyncGenerator["Redis", None]:  # type: ignore[name-defined]
    """Provide a managed Redis client for request scope."""

    client: Redis = _build_redis_client()
    try:
        yield client
    finally:
        try:
            await client.close()
        except Exception:  # noqa: BLE001 – ignore shutdown errors
            pass


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

        def dependency(user: User = Depends(auth_deps.get_current_user)):
            # Use JWT claims for role checking
            user_roles = getattr(
                user, "_current_roles", [UserRole.INDIVIDUAL_INVESTOR.value]
            )

            # Check if user has any of the required roles
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Access denied. Required roles: %s. Your roles: %s"
                        % (required_roles, user_roles)
                    ),
                )
            return user

        return dependency

    def require_attributes(self, requirements: dict[str, any]):  # noqa: D401
        """Create a dependency that enforces attribute requirements."""

        def dependency(user: User = Depends(auth_deps.get_current_user)):
            # Use JWT claims for attribute checking
            user_attributes = getattr(user, "_current_attributes", {})

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
            return user

        return dependency

    def require_permission(self, required_permission: str):  # noqa: D401
        """Create a dependency that enforces permission requirements."""

        def dependency(user: User = Depends(auth_deps.get_current_user)):
            # Use JWT claims for permission checking
            user_roles = getattr(
                user, "_current_roles", [UserRole.INDIVIDUAL_INVESTOR.value]
            )

            if not self.has_permission(user_roles, required_permission):
                user_permissions = self._expand_permissions(user_roles)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Access denied. Required permission: %s. Your permissions: %s"
                        % (required_permission, list(user_permissions))
                    ),
                )
            return user

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
