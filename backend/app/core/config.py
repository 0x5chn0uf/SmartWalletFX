from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings

from app.validators.security import SecurityValidator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Wallet Tracker"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
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
        2. Assemble from individual POSTGRES_* components.
        """

        if v:  # explicit full DSN wins
            return v

        values = info.data  # current field values collected by Pydantic

        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        server = values.get("POSTGRES_SERVER")
        port = values.get("POSTGRES_PORT")
        db = values.get("POSTGRES_DB")

        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    # External APIs
    ALCHEMY_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None

    # Password hashing
    BCRYPT_ROUNDS: int = 12  # Default cost factor for bcrypt

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
    JWT_KEYS: dict[str, str] = {}

    # Identifier of the key currently used to *sign* newly-issued tokens.
    # MUST be present in *JWT_KEYS*.
    ACTIVE_JWT_KID: str = "default"

    # Grace-period (seconds) during which tokens signed with the previous key
    # remain valid after rotation.  When 0, rotation is immediate.
    JWT_ROTATION_GRACE_PERIOD_SECONDS: int = 300

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

    # --- Backup settings ----------------------------------------------------
    BACKUP_DIR: str = "backups"  # default relative directory for CLI backups
    BACKUP_PGDUMP_PATH: str = "pg_dump"  # override if binary in custom path
    BACKUP_PGRESTORE_PATH: str = "pg_restore"  # override if binary in custom path
    BACKUP_RETENTION_DAYS: int = 7  # how many days of dumps to keep
    BACKUP_SCHEDULE_CRON: str = "0 2 * * *"  # default daily at 02:00 UTC
    BACKUP_STORAGE_ADAPTER: str = "local"  # 'local' or 's3'
    BACKUP_ENCRYPTION_ENABLED: bool = False  # set to True to enable GPG encryption
    GPG_RECIPIENT_KEY_ID: str | None = None  # required when encryption enabled
    # --- S3 / AWS (optional) ---
    BACKUP_S3_BUCKET: str | None = (
        None  # S3 bucket for backups when using the S3 adapter
    )
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_DEFAULT_REGION: str | None = "us-east-1"
    AWS_S3_ENDPOINT_URL: str | None = None  # allow custom endpoint / MinIO

    # --- Monitoring & Alerting Settings ------------------------------------
    # Prometheus metrics endpoint configuration
    PROMETHEUS_ENABLED: bool = True  # Enable/disable Prometheus metrics
    PROMETHEUS_PORT: int = 9090  # Port for Prometheus metrics server
    PROMETHEUS_HOST: str = "0.0.0.0"  # Host for Prometheus metrics server

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


settings = Settings()

"""
CoinGecko is used as the price oracle for live USD values
in the Radiant adapter.
"""
