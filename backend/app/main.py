from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.core.init_db import init_db


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    Sets up CORS, database initialization, and API routers.
    Returns:
        FastAPI: The configured FastAPI app instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url="/openapi.json",
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize database tables on startup
    @app.on_event("startup")
    async def on_startup():
        """
        FastAPI startup event handler.
        Initializes the database tables asynchronously.
        """
        await init_db()

    # Import and include API routers
    app.include_router(api_router)
    return app


app = create_app()
