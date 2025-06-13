import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Wallet Tracker"
    VERSION: str = "0.1.0"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
    ]  # React default port

    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL") or "sqlite:///app.db"

    # External APIs
    ALCHEMY_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None

    # Web3
    ARBITRUM_RPC_URL: Optional[str] = os.getenv("ARBITRUM_RPC_URL") or None
    WEB3_PROVIDER_URI: Optional[str] = os.getenv("WEB3_PROVIDER_URI") or None

    # Pydantic v2 config – ignore extra environment variables to prevent
    # validation errors when the host machine defines unrelated keys
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()

"""
CoinGecko is used as the price oracle for live USD values
in the Radiant adapter.
"""
