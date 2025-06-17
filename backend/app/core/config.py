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

    # Web3
    ARBITRUM_RPC_URL: Optional[str] = None
    WEB3_PROVIDER_URI: Optional[str] = None

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


settings = Settings()

"""
CoinGecko is used as the price oracle for live USD values
in the Radiant adapter.
"""
