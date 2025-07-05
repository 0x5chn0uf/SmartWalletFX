"""Fixture configuration and settings for the test suite."""

import os

import pytest


@pytest.fixture(scope="session")
def test_config():
    """
    Session-scoped test configuration.
    Provides centralized configuration for all test fixtures.
    """
    # ------------------------------------------------------------------
    # Database configuration – allow overriding via TEST_DB_URL so the
    # test-suite can seamlessly switch between the default in-memory
    # SQLite database and an external Postgres instance when running
    # inside Docker / CI.  We derive the *sync* URL from the async one
    # by stripping the async driver suffix ("+asyncpg" or "+aiosqlite").
    # ------------------------------------------------------------------

    async_db_url = os.environ.get("TEST_DB_URL", "sqlite+aiosqlite:///:memory:")

    if "+asyncpg" in async_db_url:
        sync_db_url = async_db_url.replace("+asyncpg", "")
    elif "+aiosqlite" in async_db_url:
        sync_db_url = async_db_url.replace("+aiosqlite", "")
    else:
        # Fallback – best-effort conversion; for Postgres this yields a
        # psycopg2 connection string, for SQLite it is identical.
        sync_db_url = async_db_url

    return {
        "database": {
            "url": async_db_url,
            "sync_url": sync_db_url,
            "echo": False,
        },
        "auth": {
            "test_password": "S3cur3!pwd",
            "jwt_secret": "test-secret-key",
            "jwt_algorithm": "HS256",
        },
        "redis": {
            "url": "redis://localhost:6379/1",
            "mock": True,
        },
        "web3": {
            "mock": True,
            "provider_url": "http://localhost:8545",
        },
        "external_services": {
            "mock_all": True,
        },
    }


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch, test_config):
    """
    Automatically mock application settings for testing.
    This fixture runs for every test to ensure consistent test environment.
    """
    # Mock database settings
    monkeypatch.setenv("DATABASE_URL", test_config["database"]["url"])
    monkeypatch.setenv("SYNC_DATABASE_URL", test_config["database"]["sync_url"])
    # Expose the async URL via TEST_DB_URL which is consumed by Alembic
    # (see backend/migrations/env.py) and some fixtures.
    monkeypatch.setenv("TEST_DB_URL", test_config["database"]["url"])

    # Mock authentication settings
    monkeypatch.setenv("JWT_SECRET_KEY", test_config["auth"]["jwt_secret"])
    monkeypatch.setenv("JWT_ALGORITHM", test_config["auth"]["jwt_algorithm"])

    # Mock Redis settings
    monkeypatch.setenv("REDIS_URL", test_config["redis"]["url"])

    # Mock external service settings
    monkeypatch.setenv(
        "MOCK_EXTERNAL_SERVICES", str(test_config["external_services"]["mock_all"])
    )

    # Mock environment-specific settings
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DEBUG", "true")

    return test_config


@pytest.fixture
def fixture_config():
    """
    Function-scoped fixture configuration.
    Allows tests to override specific configuration values.
    """
    return {
        "user": {
            "default_password": "S3cur3!pwd",
            "email_domain": "example.com",
            "username_prefix": "test.user",
        },
        "wallet": {
            "address_prefix": "0x",
            "name_prefix": "Test Wallet",
        },
        "token": {
            "address_prefix": "0x",
            "symbol_prefix": "TEST",
        },
    }


@pytest.fixture
def test_data_config():
    """
    Configuration for test data generation.
    Provides consistent patterns for creating test data.
    """
    return {
        "users": {
            "count": 5,
            "password": "S3cur3!pwd",
            "email_template": "user{index}@example.com",
            "username_template": "testuser{index}",
        },
        "wallets": {
            "count": 3,
            "address_template": "0x{hex}",
            "name_template": "Test Wallet {index}",
        },
        "tokens": {
            "count": 10,
            "address_template": "0x{hex}",
            "symbol_template": "TEST{index}",
            "name_template": "Test Token {index}",
        },
    }
