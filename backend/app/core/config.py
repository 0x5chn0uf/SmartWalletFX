from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings

from app.validators.security import SecurityValidator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Wallet Tracker"
    VERSION: str = "0.1.0"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
    ]  # React default port

    # Database
    DATABASE_URL: str = "sqlite:///./smartwallet_dev.db"

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


settings = Settings()

"""
CoinGecko is used as the price oracle for live USD values
in the Radiant adapter.
"""
