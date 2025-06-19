import uuid
from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.snapshot_aggregation import SnapshotAggregationService
from app.usecase.defi_aave_usecase import AaveUsecase
from app.usecase.defi_compound_usecase import CompoundUsecase
from app.usecase.defi_radiant_usecase import RadiantUsecase
from app.usecase.portfolio_aggregation_usecase import (
    PortfolioAggregationUsecase,
)
from app.utils.jwt import JWTUtils
from app.utils.rate_limiter import login_rate_limiter


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
        return user


# Instantiate auth deps singleton
auth_deps = AuthDeps()

# Public API – expose only the three singletons and the DB snapshot helper
get_snapshot_service = db_deps.get_snapshot_service  # convenience bound method

__all__ = [
    "db_deps",
    "blockchain_deps",
    "auth_deps",
    "get_snapshot_service",
]
