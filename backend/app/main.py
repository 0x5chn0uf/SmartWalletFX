from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError  # local import

# Import models to register them with SQLAlchemy Base
import app.models  # noqa: F401

# --- New imports for structured logging & error handling ---
from app.core.middleware import CorrelationIdMiddleware, JWTAuthMiddleware
from app.di import DIContainer
from app.domain.schemas.user import WeakPasswordError  # local import


class ApplicationFactory:
    """Factory for creating FastAPI applications with dependency injection."""

    def __init__(self, di_container: DIContainer):
        """Initialize with DIContainer."""
        self.di_container = di_container

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application instance using DIContainer."""
        config = self.di_container.get_core("config")
        core_logging = self.di_container.get_core("logging")
        core_logging.setup_logging()

        app = FastAPI(
            title=config.PROJECT_NAME,
            version=config.VERSION,
            openapi_url="/openapi.json",
        )

        # Set up CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Correlation-ID middleware (must run early)
        app.add_middleware(CorrelationIdMiddleware)

        # JWT Auth middleware (extract user_id from tokens)
        app.add_middleware(JWTAuthMiddleware)

        # Register global exception handlers
        error_handling = self.di_container.get_core("error_handling")
        app.add_exception_handler(
            Exception,
            error_handling.generic_exception_handler,  # type: ignore[arg-type]
        )
        app.add_exception_handler(
            HTTPException,
            error_handling.http_exception_handler,  # type: ignore[arg-type]
        )

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
            await self.di_container.get_core("database").init_db()

        # Register singleton endpoint routers
        self._register_singleton_routers(app)

        return app

    def _register_singleton_routers(self, app: FastAPI):
        """Register singleton endpoint routers from DIContainer."""
        email_verification_endpoint = self.di_container.get_endpoint(
            "email_verification"
        )
        oauth_endpoint = self.di_container.get_endpoint("oauth")
        wallets_endpoint = self.di_container.get_endpoint("wallets")
        defi_endpoint = self.di_container.get_endpoint("defi")
        health_endpoint = self.di_container.get_endpoint("health")
        jwks_endpoint = self.di_container.get_endpoint("jwks")
        users_endpoint = self.di_container.get_endpoint("users")
        admin_endpoint = self.di_container.get_endpoint("admin")
        password_reset_endpoint = self.di_container.get_endpoint("password_reset")
        auth_endpoint = self.di_container.get_endpoint("auth")

        # Register the singleton endpoint routers
        if email_verification_endpoint:
            app.include_router(email_verification_endpoint.ep, tags=["auth"])
        if oauth_endpoint:
            app.include_router(oauth_endpoint.ep, tags=["auth"])
        if wallets_endpoint:
            app.include_router(wallets_endpoint.ep, tags=["wallets"])
        if defi_endpoint:
            app.include_router(defi_endpoint.ep, tags=["defi"])
        if health_endpoint:
            app.include_router(health_endpoint.ep, tags=["health"])
        if jwks_endpoint:
            app.include_router(jwks_endpoint.ep, tags=["jwks"])
        if users_endpoint:
            app.include_router(users_endpoint.ep, tags=["users"])
        if admin_endpoint:
            app.include_router(admin_endpoint.ep, prefix="/admin", tags=["admin"])
        if password_reset_endpoint:
            app.include_router(password_reset_endpoint.ep, tags=["auth"])
        if auth_endpoint:
            app.include_router(auth_endpoint.ep, tags=["auth"])


# Create app using DIContainer
di_container = DIContainer()
app_factory = ApplicationFactory(di_container)
app = app_factory.create_app()


def create_app() -> FastAPI:
    """Module-level function to create FastAPI app (for backwards compatibility)."""
    container = DIContainer()
    factory = ApplicationFactory(container)
    return factory.create_app()
