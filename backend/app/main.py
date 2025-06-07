from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.api import api_router
from .core.config import settings


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app = create_application()
