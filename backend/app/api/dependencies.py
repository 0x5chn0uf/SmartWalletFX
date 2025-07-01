from __future__ import annotations

import logging as _logging
import uuid
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3

from app.core.config import settings
from app.core.database import get_db
from app.core.security.roles import ROLE_PERMISSIONS_MAP, UserRole
from app.models.user import User

# DeFi-tracker infrastructure
from app.repositories.aggregate_metrics_repository import (
    AggregateMetricsRepository,
)

# Services
from app.services.defi_aggregation_service import DeFiAggregationService
from app.services.snapshot_aggregation import SnapshotAggregationService
from app.usecase.defi_aave_usecase import AaveUsecase
from app.usecase.defi_compound_usecase import CompoundUsecase
from app.usecase.defi_radiant_usecase import RadiantUsecase
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioAggregationUsecase,
)
from app.utils.jwks_cache import _build_redis_client
from app.utils.jwt import JWTUtils
from app.utils.rate_limiter import login_rate_limiter

_logger = _logging.getLogger(__name__)


def _build_aggregator_async():
    usecase = PortfolioAggregationUsecase()

    async def _aggregator(address: str):  # type: ignore[override]
        return await usecase.aggregate_portfolio_metrics(address)

    return _aggregator


class DBDeps:  # noqa: D101 – small wrapper for DB related deps
    def __init__(self):
        # Public callables are exposed below via bound attributes
        pass

    def get_snapshot_service(
        self, db: AsyncSession = Depends(get_db)
    ) -> SnapshotAggregationService:  # pragma: no cover – simple factory
        """Return SnapshotAggregationService bound to provided DB session."""

        return SnapshotAggregationService(db, _build_aggregator_async())

    # ------------------------------------------------------------------
    # DeFi tracker repository / service providers
    # ------------------------------------------------------------------

    def get_aggregate_metrics_repo(
        self, db: AsyncSession = Depends(get_db)
    ) -> AggregateMetricsRepository:  # noqa: D401 – factory
        """Return SQLAlchemy implementation of AggregateMetricsRepository."""

        return AggregateMetricsRepository(db)


db_deps = DBDeps()


# ---------------------------------------------------------------------------
# Blockchain-related dependencies
# ---------------------------------------------------------------------------


class BlockchainDeps:
    """Group Web3 provider + protocol use-cases."""

    @lru_cache()
    def get_w3(self):  # noqa: D401 – dep factory
        default_uri = "https://ethereum-rpc.publicnode.com"
        uri = getattr(settings, "WEB3_PROVIDER_URI", default_uri)
        return Web3(Web3.HTTPProvider(uri))

    # Use-case factories -----------------------------------------------------

    def get_aave_usecase(self) -> AaveUsecase:  # noqa: D401 – dep factory
        return AaveUsecase(self.get_w3())

    def get_compound_usecase(self) -> CompoundUsecase:  # noqa: D401 – dep factory
        return CompoundUsecase(self.get_w3())

    def get_radiant_usecase(self) -> RadiantUsecase:  # noqa: D401 – dep factory
        return RadiantUsecase()

    def get_portfolio_aggregation_usecase(
        self,
    ) -> PortfolioAggregationUsecase:  # noqa: D401
        return PortfolioAggregationUsecase()


blockchain_deps = BlockchainDeps()


# ---------------------------------------------------------------------------
# Auth / security dependencies
# ---------------------------------------------------------------------------


class AuthDeps:
    """Rate-limit, OAuth2 scheme, and *current-user* helper."""

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

    async def rate_limit_auth_token(  # type: ignore[valid-type]
        self, request: Request
    ) -> None:
        """Throttle excessive login attempts per client IP (in-memory)."""

        identifier = request.client.host or "unknown"
        if not login_rate_limiter.allow(identifier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts, please try again later.",
                headers={"Retry-After": str(settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)},
            )

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        """Validate JWT *token* and return the associated :class:`User`."""

        try:
            payload = JWTUtils.decode_token(token)
        except Exception:  # noqa: BLE001 – translate
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            pk = uuid.UUID(str(sub))
        except ValueError:
            if str(sub).isdigit():
                pk = int(sub)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid subject in token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        user = await db.get(User, pk)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract role and attribute information from JWT claims for RBAC/ABAC
        # This provides backward compatibility for tokens without role claims
        token_roles = payload.get("roles", [UserRole.INDIVIDUAL_INVESTOR.value])
        token_attributes = payload.get("attributes", {})

        # Add extracted claims as runtime attributes (not persisted)
        # Authorization deps rely on these runtime props for RBAC/ABAC checks
        user._current_roles = token_roles
        user._current_attributes = token_attributes

        return user


# Instantiate auth deps singleton
auth_deps = AuthDeps()

# Public API – expose only the singletons and the DB snapshot helper
get_snapshot_service = db_deps.get_snapshot_service  # convenience bound method
get_aggregate_metrics_repo = db_deps.get_aggregate_metrics_repo

__all__ = [
    "db_deps",
    "blockchain_deps",
    "auth_deps",
    "get_redis",
    "get_snapshot_service",
    "get_aggregate_metrics_repo",
    "get_aggregator_service",
]

# ---------------------------------------------------------------------------
# Redis dependency
# ---------------------------------------------------------------------------


@asynccontextmanager
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


async def get_aggregator_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> DeFiAggregationService:
    """Return DeFiAggregationService with database and Redis dependencies."""
    return DeFiAggregationService(db, redis)


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

# ---------------------------------------------------------------------------
# Expose helpers at module level for backward compatibility
# ---------------------------------------------------------------------------

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
