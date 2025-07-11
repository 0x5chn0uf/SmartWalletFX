from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError  # local import

from app.api.api import api_router
from app.core import error_handling
from app.core.init_db import init_db
from app.core.services import ServiceContainer
from app.core.database import container as default_container

# --- New imports for structured logging & error handling ---
from app.core.logging import setup_logging  # noqa: F401 – side-effect import
from app.core.middleware import CorrelationIdMiddleware
from app.utils import audit  # noqa: F401


def create_app(container: ServiceContainer | None = None) -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    Sets up CORS, database initialization, and API routers.
    Returns:
        FastAPI: The configured FastAPI app instance.
    """
    cont = container or default_container

    app = FastAPI(
        title=cont.settings.PROJECT_NAME,
        version=cont.settings.VERSION,
        openapi_url="/openapi.json",
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cont.settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Correlation-ID middleware (must run early)
    app.add_middleware(CorrelationIdMiddleware)

    # Register global exception handlers
    app.add_exception_handler(
        Exception,
        error_handling.generic_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        HTTPException,
        error_handling.http_exception_handler,  # type: ignore[arg-type]
    )
    from fastapi.exceptions import RequestValidationError  # local import

    app.add_exception_handler(
        RequestValidationError,  # type: ignore[arg-type]
        error_handling.validation_exception_handler,
    )

    app.add_exception_handler(
        IntegrityError,
        error_handling.integrity_error_handler,  # type: ignore[arg-type]
    )

    # Initialize database tables on startup
    @app.on_event("startup")
    async def on_startup() -> None:
        """
        FastAPI startup event handler.
        Initializes the database tables asynchronously.
        """
        await init_db()

    # Import and include API routers
    app.include_router(api_router)
    return app


container = default_container
app = create_app(container)
