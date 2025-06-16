from fastapi import APIRouter

from app.api.endpoints import auth, defi, health, wallets

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(wallets.router, tags=["wallets"])
api_router.include_router(defi.router, tags=["defi"])
api_router.include_router(auth.router, tags=["auth"])
