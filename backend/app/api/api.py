from fastapi import APIRouter

from app.api.endpoints import admin as admin_rbac
from app.api.endpoints import (
    admin_db,
    audit_logs,
    auth,
    defi,
    health,
    jwks,
    oauth,
    password_reset,
    users,
    wallets,
)
from app.core.services import ServiceContainer


def create_api_router(container: ServiceContainer) -> APIRouter:
    router = APIRouter()
    router.include_router(health.router, tags=["health"])
    router.include_router(wallets.get_router(container), tags=["wallets"])
    router.include_router(defi.router, tags=["defi"])
    router.include_router(auth.router, tags=["auth"])
    router.include_router(oauth.router, tags=["auth"])
    router.include_router(password_reset.router, tags=["auth"])
    router.include_router(users.router, tags=["users"])
    router.include_router(jwks.router, tags=["jwks"])
    router.include_router(audit_logs.router, tags=["audit-logs"])
    router.include_router(
        admin_db.router, prefix="/admin/db", tags=["admin", "database"]
    )
    router.include_router(admin_rbac.router, prefix="/admin", tags=["admin"])
    return router


__all__ = ["create_api_router"]
