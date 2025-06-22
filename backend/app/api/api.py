from fastapi import APIRouter

from app.api.endpoints import (
    admin_db,
    auth,
    defi,
    health,
    jwks,
    users,
    wallets,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(wallets.router, tags=["wallets"])
api_router.include_router(defi.router, tags=["defi"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(jwks.router, tags=["jwks"])
api_router.include_router(
    admin_db.router, prefix="/admin/db", tags=["admin", "database"]
)
