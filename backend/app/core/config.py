from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings

from app.validators.security import SecurityValidator


class Configuration(BaseSettings):
    """Configuration service for application settings as singleton."""

    PROJECT_NAME: str = "SmartWalletFX"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
    ]  # Frontend development servers

    # ------------------------------------------------------------------
    # Database – assemble DATABASE_URL from individual parts when not
    # provided explicitly.  This mirrors the pattern recommended by the
    # FastAPI SQLAlchemy guides and makes it trivial for developers to
    # override *either* the complete connection string (e.g. via a cloud
    # secret) *or* individual bits such as user/password while retaining
    # sensible defaults for local development.
    # ------------------------------------------------------------------

    # Full connection string takes precedence if defined in the environment
    DATABASE_URL: str | None = None
    TEST_DB_URL: str = (
        "postgresql+asyncpg://testuser:testpass@localhost:55432/smartwallet_test"
    )

    # Individual components (used when DATABASE_URL is missing)
    POSTGRES_USER: str = "devuser"
    POSTGRES_PASSWORD: str = "devpass"
    POSTGRES_SERVER: str = "postgres-dev"  # host name in docker-compose
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "smartwallet_dev"

    # Connection pool settings (only relevant for sync engines or for async
    # pooling via SQLAlchemy – keep defaults modest for dev/tests).
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _assemble_db_connection(cls, v: str | None, info):  # noqa: D401
        """Return a fully qualified SQLAlchemy *async* URL.

        The value precedence is:

        1. Explicit ``DATABASE_URL`` env var / .env (if *truthy*)
        2. ``TEST_DB_URL`` env var if in test environment (if *truthy*)
        3. Assemble from individual POSTGRES_* components.
        """
        import os

        if v:  # explicit full DSN wins
            return v

        # Always prefer TEST_DB_URL when explicitly provided – this is primarily
        # set by the test suite's fixtures (see *tests/shared/fixtures/base.py*)
        # to point the application at a temporary SQLite or PostgreSQL database.
        #
        # Previously, this value was only honoured when PyTest-specific
        # environment variables were already set.  However, those variables are
        # not available at *import-time* when the FastAPI app (and therefore
        # the Configuration singleton) is instantiated, which caused the
        # application to fall back to the default Postgres connection string
        # and fail during the test startup phase.
        #
        # By unconditionally returning ``TEST_DB_URL`` when it is present we
        # ensure that the correct temporary database is used regardless of the
        # import order or execution context.
        test_db_url = os.getenv("TEST_DB_URL")
        if test_db_url:
            return test_db_url

        values = info.data  # current field values collected by Pydantic

        # Use default values when not provided in environment or values dict
        user = values.get("POSTGRES_USER") or "devuser"
        password = values.get("POSTGRES_PASSWORD") or "devpass"
        server = values.get("POSTGRES_SERVER") or "postgres-dev"
        port = values.get("POSTGRES_PORT") or 5432
        db = values.get("POSTGRES_DB") or "smartwallet_dev"

        # Guard against missing or invalid port coming from environment vars
        if (not port) or (isinstance(port, str) and port.lower() == "none"):
            port = 5432

        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    # External APIs
    ALCHEMY_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None

    # Password hashing
    BCRYPT_ROUNDS: int = 12  # Default cost factor for bcrypt

    # GPG encryption
    GPG_RECIPIENT_KEY_ID: Optional[str] = None

    # JWT configuration
    JWT_ALGORITHM: str = "HS256"
    JWT_PRIVATE_KEY_PATH: Optional[str] = None
    JWT_PUBLIC_KEY_PATH: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_SECRET_KEY: Optional[str] = "insecure-test-key"

    # Authentication rate-limiting (login attempts)
    AUTH_RATE_LIMIT_ATTEMPTS: int = 5  # max attempts per window
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60  # rolling window size

    # Web3
    ARBITRUM_RPC_URL: Optional[str] = None
    WEB3_PROVIDER_URI: Optional[str] = None

    # Redis
    REDIS_URL: Optional[str] = None

    # Frontend base URL used for OAuth success redirects
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # OAuth provider credentials
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    OAUTH_REDIRECT_URI: str = "http://localhost:8000/auth/oauth/{provider}/callback"

    # --- Key-Rotation Support ---------------------------
    # Mapping of key-id (kid) → PEM/secret used for verifying signatures.
    # In HS* algorithms the value is the raw secret; for RS* algorithms the
    # value should be the *public* key PEM string.  The active signing key is
    # controlled by *ACTIVE_JWT_KID*.  Additional keys may exist in the map
    # during a grace-period following rotation so that previously-issued
    # tokens remain valid.
    JWT_KEYS: dict[str, str] = {"default": "insecure-test-key"}

    # Identifier of the key currently used to *sign* newly-issued tokens.
    # MUST be present in *JWT_KEYS*.
    ACTIVE_JWT_KID: str = "default"

    # Grace-period (seconds) during which tokens signed with the previous key
    # remain valid after rotation.  When 0, rotation is immediate.
    JWT_ROTATION_GRACE_PERIOD_SECONDS: int = 300

    # Email configuration
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = False  # STARTTLS
    SMTP_USE_SSL: bool = False  # SMTPS (implicit TLS)
    EMAIL_FROM: str = "no-reply@smartwalletfx.local"  # Default From header

    # --- Celery Beat Schedules & Locks ---------------------------------
    # Cron expression for the automated JWT key rotation task.
    JWT_ROTATION_SCHEDULE_CRON: str = "*/5 * * * *"  # default: every 5 minutes

    # TTL (seconds) for the Redis lock ensuring single-worker execution.
    JWT_ROTATION_LOCK_TTL_SEC: int = 600  # default: 10 minutes

    # JWKS caching configuration
    JWKS_CACHE_TTL_SEC: int = 3600  # 1 hour default TTL

    # Pydantic v2 config – ignore extra environment variables to prevent
    # validation errors when the host machine defines unrelated keys
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore",
    }

    # --- Validators -----------------------------------------------------

    @field_validator("BCRYPT_ROUNDS", mode="before")
    @classmethod
    def _validate_rounds(cls, v: int | str) -> int:
        """Delegate to SecurityValidator.bcrypt_rounds for validation."""

        return SecurityValidator.bcrypt_rounds(v)

    # --- Monitoring & Alerting Settings ------------------------------------
    # Prometheus metrics endpoint configuration
    PROMETHEUS_ENABLED: bool = True  # Enable/disable Prometheus metrics
    PROMETHEUS_PORT: int = 9090  # Port for Prometheus metrics server
    # Host for Prometheus metrics server – binding to all interfaces is
    # intentional inside containerized deployments to allow scrape from
    # the host machine or other services.
    PROMETHEUS_HOST: str = "0.0.0.0"  # nosec B104

    # JWT rotation alerting thresholds
    JWT_ROTATION_ALERT_ON_ERROR: bool = True  # Send alerts on rotation errors
    JWT_ROTATION_ALERT_ON_RETRY: bool = False  # Send alerts on retries

    # ------------------------------------------------------------------
    # Email / SMTP configuration  (used by EmailService for outgoing mail)
    # ------------------------------------------------------------------

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = False  # STARTTLS
    SMTP_USE_SSL: bool = False  # SMTPS (implicit TLS)
    EMAIL_FROM: str = "no-reply@smartwalletfx.local"  # Default From header

    @property
    def redis_url(self) -> str:
        """Get Redis URL with fallback to default localhost."""
        return self.REDIS_URL or "redis://localhost:6379/0"
