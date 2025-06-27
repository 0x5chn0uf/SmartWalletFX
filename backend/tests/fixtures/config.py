"""Fixture configuration and settings for the test suite."""

import os
from typing import Any, Dict

import pytest


@pytest.fixture(scope="session")
def test_config():
    """
    Session-scoped test configuration.
    Provides centralized configuration for all test fixtures.
    """
    return {
        "database": {
            "url": "sqlite+aiosqlite:///:memory:",
            "sync_url": "sqlite:///:memory:",
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
