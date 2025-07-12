from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError  # local import

from app.api.api import api_router
from app.core import error_handling
from app.core.config import ConfigurationService, settings
from app.core.database import DatabaseService
from app.core.init_db import init_db

# --- New imports for structured logging & error handling ---
from app.core.logging import setup_logging  # noqa: F401 – side-effect import
from app.core.middleware import CorrelationIdMiddleware
from app.di import DIContainer
from app.schemas.user import WeakPasswordError  # local import
from app.utils import audit  # noqa: F401


class ApplicationFactory:
    """Factory for creating FastAPI applications with dependency injection."""

    def __init__(self, di_container: DIContainer):
        """Initialize with DIContainer."""
        self.di_container = di_container

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application instance using DIContainer."""
        config_service = self.di_container.get_service("config")
        database_service = self.di_container.get_service("database")

        app = FastAPI(
            title=config_service.PROJECT_NAME,
            version=config_service.VERSION,
            openapi_url="/openapi.json",
        )

        # Set up CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config_service.BACKEND_CORS_ORIGINS,
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

        app.add_exception_handler(
            WeakPasswordError, error_handling.weak_password_error_handler
        )

        # Initialize database tables on startup
        @app.on_event("startup")
        async def on_startup() -> None:
            """FastAPI startup event handler."""
            await init_db(database_service)

        # Register singleton endpoint routers
        self._register_singleton_routers(app)

        return app

    def _register_singleton_routers(self, app: FastAPI):
        """Register singleton endpoint routers from DIContainer."""
        # Get singleton endpoint instances from DIContainer
        email_verification_endpoint = self.di_container.get_endpoint(
            "email_verification"
        )
        oauth_endpoint = self.di_container.get_endpoint("oauth")
        wallets_endpoint = self.di_container.get_endpoint("wallets")
        health_endpoint = self.di_container.get_endpoint("health")
        jwks_endpoint = self.di_container.get_endpoint("jwks")
        users_endpoint = self.di_container.get_endpoint("users")
        admin_db_endpoint = self.di_container.get_endpoint("admin_db")
        admin_endpoint = self.di_container.get_endpoint("admin")

        # Register the singleton endpoint routers
        if email_verification_endpoint:
            app.include_router(email_verification_endpoint.ep, tags=["auth"])
        if oauth_endpoint:
            app.include_router(oauth_endpoint.ep, tags=["auth"])
        if wallets_endpoint:
            app.include_router(wallets_endpoint.ep, tags=["wallets"])
        if health_endpoint:
            app.include_router(health_endpoint.ep, tags=["health"])
        if jwks_endpoint:
            app.include_router(jwks_endpoint.ep, tags=["jwks"])
        if users_endpoint:
            app.include_router(users_endpoint.ep, tags=["users"])
        if admin_db_endpoint:
            app.include_router(
                admin_db_endpoint.ep, prefix="/admin/db", tags=["admin", "database"]
            )
        if admin_endpoint:
            app.include_router(admin_endpoint.ep, prefix="/admin", tags=["admin"])

        # TODO: Add other singleton endpoints as they are implemented
        # password_reset_endpoint = self.di_container.get_endpoint("password_reset")
        # auth_endpoint = self.di_container.get_endpoint("auth")
        # if password_reset_endpoint:
        #     app.include_router(password_reset_endpoint.ep, tags=["auth"])
        # if auth_endpoint:
        #     app.include_router(auth_endpoint.ep, tags=["auth"])

        # For now, include the legacy API router for endpoints not yet refactored
        app.include_router(api_router)


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

    # Correlation-ID middleware (must run early)
    app.add_middleware(CorrelationIdMiddleware)

    # Register global exception handlers
    app.add_exception_handler(
        Exception, error_handling.generic_exception_handler  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        HTTPException, error_handling.http_exception_handler  # type: ignore[arg-type]
    )
    from fastapi.exceptions import RequestValidationError  # local import

    app.add_exception_handler(
        RequestValidationError,  # type: ignore[arg-type]
        error_handling.validation_exception_handler,
    )

    app.add_exception_handler(
        IntegrityError, error_handling.integrity_error_handler  # type: ignore[arg-type]
    )

    app.add_exception_handler(
        WeakPasswordError, error_handling.weak_password_error_handler
    )

    # Initialize database tables on startup
    @app.on_event("startup")
    async def on_startup() -> None:
        """
        FastAPI startup event handler.
        Initializes the database tables asynchronously.
        """
        # Create database service instance for initialization
        config_service = ConfigurationService()
        database_service = DatabaseService(config_service)
        await init_db(database_service)

    # Import and include API routers
    app.include_router(api_router)
    return app


# Create app using DIContainer (new approach)
di_container = DIContainer()
app_factory = ApplicationFactory(di_container)
app = app_factory.create_app()

# Keep legacy app creation for backward compatibility
# app = create_app()
