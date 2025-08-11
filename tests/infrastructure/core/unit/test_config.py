import os

import pytest

from app.core.config import Configuration


def test_assemble_db_connection_defaults(monkeypatch):
    """When no env vars are set Configuration should build default Postgres URL."""
    # Clear env vars
    for var in [
        "DATABASE_URL",
        "TEST_DB_URL",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_SERVER",
        "POSTGRES_PORT",
        "POSTGRES_DB",
    ]:
        monkeypatch.delenv(var, raising=False)

    cfg = Configuration()
    url = cfg.DATABASE_URL
    assert url.endswith("/smartwallet_dev")


def test_assemble_db_connection_env_override(monkeypatch):
    """DATABASE_URL env var should override all other settings."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://foo:bar@db:5432/foo")
    cfg = Configuration()
    assert cfg.DATABASE_URL == "postgresql+asyncpg://foo:bar@db:5432/foo"
