from fastapi import APIRouter

from app.api.endpoints import health, wallets

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(wallets.router, tags=["wallets"])
