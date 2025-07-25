"""
Test Database Configuration and Management.

This module provides comprehensive database setup for integration tests:
1. Docker-based test database management
2. Automatic schema creation and cleanup
3. Transaction-based test isolation
4. Multiple database backend support
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import docker
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.config import Configuration
from app.models import Base


class TestDatabaseManager:
    """Manages test database lifecycle and configuration."""

    def __init__(self, use_docker: bool = True):
        """Initialize test database manager.

        Args:
            use_docker: Whether to use Docker for test database
        """
        self.use_docker = use_docker
        self.docker_client = None
        self.test_container = None
        self.test_engine: Optional[AsyncEngine] = None
        self.test_config: Optional[Configuration] = None

    async def setup(self) -> Configuration:
        """Set up test database and return configuration."""
        if self.use_docker:
            await self._setup_docker_database()
        else:
            await self._setup_local_database()

        return self.test_config

    async def teardown(self):
        """Clean up test database resources."""
        if self.test_engine:
            await self.test_engine.dispose()

        if self.use_docker and self.test_container:
            await self._cleanup_docker_database()

    async def _setup_docker_database(self):
        """Set up Docker-based test database."""
        try:
            self.docker_client = docker.from_env()
        except Exception:
            # Fall back to local database if Docker is not available
            await self._setup_local_database()
            return

        # Check if test database container already exists
        container_name = "smartwallet_test_db"

        try:
            self.test_container = self.docker_client.containers.get(container_name)
            if self.test_container.status != "running":
                self.test_container.start()
        except docker.errors.NotFound:
            # Create new test database container
            self.test_container = self.docker_client.containers.run(
                "postgres:15",
                name=container_name,
                environment={
                    "POSTGRES_USER": "testuser",
                    "POSTGRES_PASSWORD": "testpass",
                    "POSTGRES_DB": "test_smartwallet",
                },
                ports={"5432/tcp": None},  # Let Docker assign a port
                detach=True,
                remove=False,  # Keep container for reuse
            )

        # Wait for database to be ready
        await self._wait_for_database_ready()

        # Get the assigned port
        port_info = self.docker_client.api.port(self.test_container.id, 5432)
        host_port = port_info[0]["HostPort"]

        # Create test configuration
        test_db_url = f"postgresql+asyncpg://testuser:testpass@localhost:{host_port}/test_smartwallet"
        self.test_config = Configuration()
        self.test_config.DATABASE_URL = test_db_url
        self.test_config.BCRYPT_ROUNDS = 4  # Fast for tests

        # Create engine and set up schema
        self.test_engine = create_async_engine(test_db_url, echo=False)
        await self._create_test_schema()

    async def _setup_local_database(self):
        """Set up local SQLite test database."""
        # Use in-memory SQLite for fast unit testing
        test_db_url = "sqlite+aiosqlite:///:memory:"

        self.test_config = Configuration()
        self.test_config.DATABASE_URL = test_db_url
        self.test_config.BCRYPT_ROUNDS = 4  # Fast for tests

        self.test_engine = create_async_engine(test_db_url, echo=False)
        await self._create_test_schema()

    async def _wait_for_database_ready(self, max_attempts: int = 30):
        """Wait for Docker database to be ready to accept connections."""
        for attempt in range(max_attempts):
            try:
                # Check if container is running
                self.test_container.reload()
                if self.test_container.status != "running":
                    await asyncio.sleep(1)
                    continue

                # Try to connect to the database
                port_info = self.docker_client.api.port(self.test_container.id, 5432)
                if not port_info:
                    await asyncio.sleep(1)
                    continue

                host_port = port_info[0]["HostPort"]
                test_url = f"postgresql+asyncpg://testuser:testpass@localhost:{host_port}/test_smartwallet"

                test_engine = create_async_engine(test_url)
                async with test_engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                await test_engine.dispose()

                return  # Success!

            except Exception:
                await asyncio.sleep(1)

        raise RuntimeError("Test database failed to become ready within timeout")

    async def _create_test_schema(self):
        """Create database schema for testing."""
        async with self.test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _cleanup_docker_database(self):
        """Clean up Docker test database."""
        if self.test_container:
            try:
                # Stop container but don't remove it for reuse
                self.test_container.stop()
            except Exception:
                pass  # Container might already be stopped

    @asynccontextmanager
    async def get_test_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a test database session with transaction rollback."""
        if not self.test_engine:
            raise RuntimeError("Test database not set up")

        async_session = sessionmaker(
            self.test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Start a transaction
            async with session.begin():
                try:
                    yield session
                finally:
                    # Always rollback to ensure test isolation
                    await session.rollback()


# Global test database manager instance
_test_db_manager: Optional[TestDatabaseManager] = None


async def get_test_database_manager(use_docker: bool = None) -> TestDatabaseManager:
    """Get or create the global test database manager."""
    global _test_db_manager

    if _test_db_manager is None:
        # Determine whether to use Docker based on environment
        if use_docker is None:
            use_docker = os.getenv("USE_DOCKER_TESTS", "true").lower() == "true"

        _test_db_manager = TestDatabaseManager(use_docker=use_docker)
        await _test_db_manager.setup()

    return _test_db_manager


@pytest_asyncio.fixture(scope="session")
async def test_database_manager():
    """Session-scoped test database manager."""
    manager = await get_test_database_manager()
    yield manager
    await manager.teardown()


@pytest_asyncio.fixture
async def test_database_session(test_database_manager):
    """Provide an isolated test database session."""
    async with test_database_manager.get_test_session() as session:
        yield session


@pytest.fixture
def test_database_config(test_database_manager):
    """Provide test database configuration."""
    return test_database_manager.test_config


# Convenience fixtures for different test scenarios
@pytest_asyncio.fixture
async def integration_test_session(test_database_manager):
    """Alias for test_database_session for clarity in integration tests."""
    async with test_database_manager.get_test_session() as session:
        yield session


@pytest.fixture(scope="session")
def docker_test_database():
    """Force Docker-based test database for integration tests."""

    async def _setup():
        manager = TestDatabaseManager(use_docker=True)
        await manager.setup()
        return manager

    return asyncio.run(_setup())


@pytest.fixture(scope="session")
def sqlite_test_database():
    """Force SQLite-based test database for unit tests."""

    async def _setup():
        manager = TestDatabaseManager(use_docker=False)
        await manager.setup()
        return manager

    return asyncio.run(_setup())
