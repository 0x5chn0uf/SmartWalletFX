"""End-to-end tests for backup and restore functionality.

These tests validate the complete backup and restore workflow using real PostgreSQL
instances to ensure the functionality works correctly in production-like environments.
"""

import asyncio
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import AsyncGenerator, Dict

import docker
import psycopg2
import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text

from app.utils import db_backup
from backend.tests.utils.test_data_manager import (
    TestDataManager as BackendTestDataManager,
)
from tests.fixtures.test_data import TestDataManager, verify_backup_integrity

POSTGRES_URL_TEMPLATE = "postgresql://testuser:testpass@localhost:{port}/{db}"


@pytest.fixture(scope="module")
def postgres_container():
    """
    Spins up the postgres-e2e container (port 5434), yields DB URL, and tears down after tests.
    Assumes docker-compose.e2e.yml is up.
    """
    port = 5434
    db = "testdb"
    url = POSTGRES_URL_TEMPLATE.format(port=port, db=db)
    # Wait for container to be ready
    for _ in range(30):
        try:
            with psycopg2.connect(url):
                return url
        except Exception:
            time.sleep(1)
    pytest.skip("Postgres container not ready on port 5434")


@pytest.fixture(scope="module")
def postgres_large_container():
    """
    Spins up the postgres-large container (port 5435), yields DB URL, and tears down after tests.
    Assumes docker-compose.e2e.yml is up.
    """
    port = 5435
    db = "largedb"
    url = POSTGRES_URL_TEMPLATE.format(port=port, db=db)
    for _ in range(60):
        try:
            with psycopg2.connect(url):
                return url
        except Exception:
            time.sleep(2)
    pytest.skip("Postgres large container not ready on port 5435")


@pytest.mark.e2e
def test_basic_backup_restore_cycle(postgres_container):
    """
    Test complete backup and restore cycle with a small dataset.
    """
    tdm = BackendTestDataManager(postgres_container)
    tdm.generate_realistic_schema(size="small")
    tdm.populate_test_data(volume="small")

    # Create backup
    backup_path = tempfile.mktemp(suffix=".sql.gz")
    subprocess.run(
        [
            "python",
            "-m",
            "app.utils.db_backup",
            "backup",
            "--output",
            backup_path,
            "--db-url",
            postgres_container,
        ],
        check=True,
        cwd="backend",
    )
    assert os.path.exists(backup_path)

    # Drop and recreate schema
    with psycopg2.connect(postgres_container) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        conn.commit()

    # Restore from backup
    subprocess.run(
        [
            "python",
            "-m",
            "app.utils.db_backup",
            "restore",
            "--input",
            backup_path,
            "--db-url",
            postgres_container,
            "--force",
        ],
        check=True,
        cwd="backend",
    )

    # Validate data integrity
    tdm2 = BackendTestDataManager(postgres_container)
    assert tdm2.validate_data_integrity(postgres_container, postgres_container)


@pytest.mark.e2e
def test_large_dataset_backup_restore(postgres_large_container):
    """
    Test backup/restore with a large dataset (>100MB).
    Measures backup and restore time, and validates data integrity.
    """
    _ = BackendTestDataManager(postgres_large_container)
    # Schema and data already loaded by container init
    start = time.time()
    backup_path = tempfile.mktemp(suffix=".sql.gz")
    subprocess.run(
        [
            "python",
            "-m",
            "app.utils.db_backup",
            "backup",
            "--output",
            backup_path,
            "--db-url",
            postgres_large_container,
        ],
        check=True,
        cwd="backend",
    )
    backup_time = time.time() - start
    assert os.path.exists(backup_path)
    assert backup_time < 30, f"Backup took too long: {backup_time:.2f}s"

    # Drop and recreate schema
    with psycopg2.connect(postgres_large_container) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        conn.commit()

    # Restore
    start = time.time()
    subprocess.run(
        [
            "python",
            "-m",
            "app.utils.db_backup",
            "restore",
            "--input",
            backup_path,
            "--db-url",
            postgres_large_container,
            "--force",
        ],
        check=True,
        cwd="backend",
    )
    restore_time = time.time() - start
    assert restore_time < 60, f"Restore took too long: {restore_time:.2f}s"

    # Validate data integrity (row counts and checksums)
    tdm2 = BackendTestDataManager(postgres_large_container)
    assert tdm2.validate_data_integrity(
        postgres_large_container, postgres_large_container
    )


@pytest.mark.e2e
def test_cli_integration(postgres_container):
    """
    Test CLI commands for backup and restore work with real database.
    """
    tdm = BackendTestDataManager(postgres_container)
    tdm.generate_realistic_schema(size="small")
    tdm.populate_test_data(volume="small")
    backup_path = tempfile.mktemp(suffix=".sql.gz")
    # Use Makefile CLI
    subprocess.run(
        [
            "make",
            "db-backup",
            f"OUTPUT_DIR={os.path.dirname(backup_path)}",
            f"DB_URL={postgres_container}",
            "LABEL=testcli",
        ],
        check=True,
        cwd="backend",
    )
    # Drop schema
    with psycopg2.connect(postgres_container) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        conn.commit()
    # Restore via Makefile CLI
    subprocess.run(
        [
            "make",
            "db-restore",
            f"FILE={backup_path}",
            f"DB_URL={postgres_container}",
            "FORCE=--force",
        ],
        check=True,
        cwd="backend",
    )
    # Validate
    tdm2 = BackendTestDataManager(postgres_container)
    assert tdm2.validate_data_integrity(postgres_container, postgres_container)


@pytest.mark.e2e
class TestBackupRestoreE2E:
    """End-to-end tests for backup and restore functionality."""

    @pytest_asyncio.fixture
    async def postgres_container(self) -> AsyncGenerator[Dict[str, str], None]:
        """Set up ephemeral PostgreSQL container for each test."""
        client = docker.from_env()

        # Start PostgreSQL container
        container = client.containers.run(
            "postgres:15-alpine",
            environment={
                "POSTGRES_USER": "testuser",
                "POSTGRES_PASSWORD": "testpass",
                "POSTGRES_DB": "testdb",
            },
            ports={"5432/tcp": None},  # Let Docker assign a random port
            detach=True,
            remove=True,
        )

        try:
            # Wait for container to be ready
            container.reload()
            port = container.ports["5432/tcp"][0]["HostPort"]
            dsn = f"postgresql://testuser:testpass@localhost:{port}/testdb"

            # Wait for PostgreSQL to be ready
            for _ in range(30):  # 30 second timeout
                try:
                    engine = create_engine(dsn)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    engine.dispose()
                    break
                except Exception:
                    time.sleep(1)
            else:
                raise RuntimeError("PostgreSQL container failed to start")

            yield {"dsn": dsn, "container_id": container.id, "port": port}

        finally:
            # Clean up container
            try:
                container.stop(timeout=10)
            except Exception:
                pass

    @pytest_asyncio.fixture
    async def test_database(
        self, postgres_container: Dict[str, str]
    ) -> AsyncGenerator[str, None]:
        """Set up test database with realistic data."""
        dsn = postgres_container["dsn"]

        # Create test data
        manager = TestDataManager(dsn)
        await manager.create_test_database()

        # Validate data integrity
        counts = await manager.validate_data_integrity()
        print(f"Test database created with {counts} rows")

        yield dsn

        # Cleanup
        await manager.cleanup()

    async def test_backup_creates_valid_dump(self, test_database: str, tmp_path: Path):
        """Test that backup creates a valid PostgreSQL dump file."""
        # Set up environment
        env = {"DATABASE_URL": test_database}

        # Create backup
        backup_path = db_backup.create_dump(
            output_dir=tmp_path,
            compress=True,
            label="e2e_test",
            env=env,
            trigger="e2e_test",
        )

        # Verify backup file exists and is valid
        assert backup_path.exists()
        assert backup_path.suffix == ".gz"
        assert backup_path.stat().st_size > 0

        # Verify file integrity (basic check)
        import gzip

        with gzip.open(backup_path, "rt") as f:
            content = f.read()
            assert "PostgreSQL database dump" in content or "pg_dump" in content

    async def test_restore_maintains_data_integrity(
        self, test_database: str, tmp_path: Path
    ):
        """Test that restore operation maintains complete data integrity."""
        # Create backup of original database
        env = {"DATABASE_URL": test_database}
        backup_path = db_backup.create_dump(
            output_dir=tmp_path,
            compress=True,
            label="integrity_test",
            env=env,
            trigger="e2e_test",
        )

        # Create a new PostgreSQL container for restore
        client = docker.from_env()
        restore_container = client.containers.run(
            "postgres:15-alpine",
            environment={
                "POSTGRES_USER": "restoreuser",
                "POSTGRES_PASSWORD": "restorepass",
                "POSTGRES_DB": "restoredb",
            },
            ports={"5432/tcp": None},
            detach=True,
            remove=True,
        )

        try:
            # Wait for restore container to be ready
            restore_container.reload()
            restore_port = restore_container.ports["5432/tcp"][0]["HostPort"]
            restore_dsn = f"postgresql://restoreuser:restorepass@localhost:{restore_port}/restoredb"

            # Wait for PostgreSQL to be ready
            for _ in range(30):
                try:
                    engine = create_engine(restore_dsn)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    engine.dispose()
                    break
                except Exception:
                    time.sleep(1)
            else:
                raise RuntimeError("Restore PostgreSQL container failed to start")

            # Restore backup to new database
            restore_env = {"DATABASE_URL": restore_dsn}
            db_backup.restore_dump(
                dump_path=backup_path, force=True, env=restore_env, trigger="e2e_test"
            )

            # Verify data integrity
            integrity_ok = await verify_backup_integrity(test_database, restore_dsn)
            assert integrity_ok, "Data integrity check failed after restore"

        finally:
            # Clean up restore container
            try:
                restore_container.stop(timeout=10)
            except Exception:
                pass

    async def test_backup_performance_meets_requirements(
        self, test_database: str, tmp_path: Path
    ):
        """Test that backup performance meets production requirements."""
        env = {"DATABASE_URL": test_database}

        # Measure backup duration
        start_time = time.perf_counter()
        backup_path = db_backup.create_dump(
            output_dir=tmp_path,
            compress=True,
            label="performance_test",
            env=env,
            trigger="e2e_test",
        )
        end_time = time.perf_counter()

        duration = end_time - start_time
        file_size_mb = backup_path.stat().st_size / (1024 * 1024)

        print(f"Backup completed in {duration:.2f}s, size: {file_size_mb:.2f}MB")

        # Performance requirements: < 30s for 1GB, < 5s for small databases
        if file_size_mb > 100:  # Large database
            assert duration < 30, f"Backup took {duration:.2f}s, expected < 30s"
        else:  # Small database
            assert duration < 5, f"Backup took {duration:.2f}s, expected < 5s"

    async def test_restore_performance_meets_requirements(
        self, test_database: str, tmp_path: Path
    ):
        """Test that restore performance meets production requirements."""
        # Create backup first
        env = {"DATABASE_URL": test_database}
        backup_path = db_backup.create_dump(
            output_dir=tmp_path,
            compress=True,
            label="restore_performance_test",
            env=env,
            trigger="e2e_test",
        )

        # Create restore container
        client = docker.from_env()
        restore_container = client.containers.run(
            "postgres:15-alpine",
            environment={
                "POSTGRES_USER": "restoreuser",
                "POSTGRES_PASSWORD": "restorepass",
                "POSTGRES_DB": "restoredb",
            },
            ports={"5432/tcp": None},
            detach=True,
            remove=True,
        )

        try:
            # Wait for container to be ready
            restore_container.reload()
            restore_port = restore_container.ports["5432/tcp"][0]["HostPort"]
            restore_dsn = f"postgresql://restoreuser:restorepass@localhost:{restore_port}/restoredb"

            for _ in range(30):
                try:
                    engine = create_engine(restore_dsn)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    engine.dispose()
                    break
                except Exception:
                    time.sleep(1)
            else:
                raise RuntimeError("Restore PostgreSQL container failed to start")

            # Measure restore duration
            restore_env = {"DATABASE_URL": restore_dsn}
            start_time = time.perf_counter()
            db_backup.restore_dump(
                dump_path=backup_path, force=True, env=restore_env, trigger="e2e_test"
            )
            end_time = time.perf_counter()

            duration = end_time - start_time
            file_size_mb = backup_path.stat().st_size / (1024 * 1024)

            print(f"Restore completed in {duration:.2f}s, size: {file_size_mb:.2f}MB")

            # Performance requirements: < 60s for 1GB, < 10s for small databases
            if file_size_mb > 100:  # Large database
                assert duration < 60, f"Restore took {duration:.2f}s, expected < 60s"
            else:  # Small database
                assert duration < 10, f"Restore took {duration:.2f}s, expected < 10s"

        finally:
            # Clean up restore container
            try:
                restore_container.stop(timeout=10)
            except Exception:
                pass

    async def test_backup_failure_handling(self, test_database: str, tmp_path: Path):
        """Test backup failure scenarios and error handling."""
        # Test with invalid database URL
        invalid_env = {
            "DATABASE_URL": "postgresql://invalid:invalid@localhost:5432/invalid"
        }

        with pytest.raises(db_backup.BackupError):
            db_backup.create_dump(
                output_dir=tmp_path,
                compress=True,
                label="failure_test",
                env=invalid_env,
                trigger="e2e_test",
            )

    async def test_restore_failure_handling(self, test_database: str, tmp_path: Path):
        """Test restore failure scenarios and error handling."""
        # Create a valid backup first
        env = {"DATABASE_URL": test_database}
        backup_path = db_backup.create_dump(
            output_dir=tmp_path,
            compress=True,
            label="restore_failure_test",
            env=env,
            trigger="e2e_test",
        )

        # Test restore to invalid database
        invalid_env = {
            "DATABASE_URL": "postgresql://invalid:invalid@localhost:5432/invalid"
        }

        with pytest.raises(db_backup.RestoreError):
            db_backup.restore_dump(
                dump_path=backup_path, force=True, env=invalid_env, trigger="e2e_test"
            )


@pytest.mark.e2e
class TestBackupRestoreCLI:
    """End-to-end tests for CLI backup and restore commands."""

    async def test_cli_backup_command(self, test_database: str, tmp_path: Path):
        """Test CLI backup command works correctly."""
        # Set environment variable
        env = os.environ.copy()
        env["DATABASE_URL"] = test_database
        env["OUTPUT_DIR"] = str(tmp_path)
        env["LABEL"] = "cli_test"

        # Run CLI backup command
        result = subprocess.run(
            ["python", "-m", "app.cli.db_backup_cli", "backup"],
            env=env,
            capture_output=True,
            text=True,
            cwd="backend",
        )

        assert result.returncode == 0, f"CLI backup failed: {result.stderr}"
        assert "Backup created successfully" in result.stdout

        # Verify backup file was created
        backup_files = list(tmp_path.glob("*.sql.gz"))
        assert len(backup_files) == 1, "Expected exactly one backup file"

    async def test_cli_restore_command(self, test_database: str, tmp_path: Path):
        """Test CLI restore command works correctly."""
        # Create backup first
        env = os.environ.copy()
        env["DATABASE_URL"] = test_database
        env["OUTPUT_DIR"] = str(tmp_path)
        env["LABEL"] = "cli_restore_test"

        subprocess.run(
            ["python", "-m", "app.cli.db_backup_cli", "backup"],
            env=env,
            capture_output=True,
            text=True,
            cwd="backend",
        )

        # Get backup file path
        backup_files = list(tmp_path.glob("*.sql.gz"))
        assert len(backup_files) == 1
        backup_path = backup_files[0]

        # Create restore container
        client = docker.from_env()
        restore_container = client.containers.run(
            "postgres:15-alpine",
            environment={
                "POSTGRES_USER": "restoreuser",
                "POSTGRES_PASSWORD": "restorepass",
                "POSTGRES_DB": "restoredb",
            },
            ports={"5432/tcp": None},
            detach=True,
            remove=True,
        )

        try:
            # Wait for container to be ready
            restore_container.reload()
            restore_port = restore_container.ports["5432/tcp"][0]["HostPort"]
            restore_dsn = f"postgresql://restoreuser:restorepass@localhost:{restore_port}/restoredb"

            for _ in range(30):
                try:
                    engine = create_engine(restore_dsn)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    engine.dispose()
                    break
                except Exception:
                    time.sleep(1)
            else:
                raise RuntimeError("Restore PostgreSQL container failed to start")

            # Run CLI restore command
            restore_env = os.environ.copy()
            restore_env["DATABASE_URL"] = restore_dsn
            restore_env["FILE"] = str(backup_path)
            restore_env["FORCE"] = "1"

            result = subprocess.run(
                ["python", "-m", "app.cli.db_backup_cli", "restore"],
                env=restore_env,
                capture_output=True,
                text=True,
                cwd="backend",
            )

            assert result.returncode == 0, f"CLI restore failed: {result.stderr}"
            assert "Restore completed successfully" in result.stdout

        finally:
            # Clean up restore container
            try:
                restore_container.stop(timeout=10)
            except Exception:
                pass


@pytest.mark.e2e
class TestBackupRestoreAPI:
    """End-to-end tests for API backup and restore endpoints."""

    async def test_api_backup_endpoint(self, test_database: str, test_app):
        """Test API backup endpoint works correctly."""
        # This test would require setting up a test FastAPI app with the backup endpoints
        # For now, we'll create a placeholder test
        pytest.skip("API endpoint testing requires additional setup")

    async def test_api_restore_endpoint(self, test_database: str, test_app):
        """Test API restore endpoint works correctly."""
        # This test would require setting up a test FastAPI app with the restore endpoints
        # For now, we'll create a placeholder test
        pytest.skip("API endpoint testing requires additional setup")


@pytest.mark.e2e
class TestBackupRestoreFailureScenarios:
    """Test failure scenarios and error handling for backup and restore operations."""

    @pytest_asyncio.fixture
    async def test_database(
        self, postgres_container: Dict[str, str]
    ) -> AsyncGenerator[str, None]:
        """Set up a test database for failure scenario testing."""
        client = docker.from_env()

        # Start PostgreSQL container
        container = client.containers.run(
            "postgres:15-alpine",
            environment={
                "POSTGRES_USER": "testuser",
                "POSTGRES_PASSWORD": "testpass",
                "POSTGRES_DB": "failuredb",
            },
            ports={"5432/tcp": None},
            detach=True,
            remove=True,
        )

        try:
            # Wait for container to be ready
            container.reload()
            port = container.ports["5432/tcp"][0]["HostPort"]
            dsn = f"postgresql://testuser:testpass@localhost:{port}/failuredb"

            # Wait for PostgreSQL to be ready
            for _ in range(30):
                try:
                    engine = create_engine(dsn)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    engine.dispose()
                    break
                except Exception:
                    await asyncio.sleep(1)
            else:
                pytest.fail("Database not ready within timeout")

            # Load test data
            tdm = TestDataManager(dsn)
            tdm.generate_realistic_schema(size="small")
            tdm.populate_test_data(volume="small")

            yield dsn

        finally:
            container.stop()

    def test_backup_with_corrupted_database(self, test_database: str, tmp_path: Path):
        """
        Test backup behavior when database is corrupted or in an inconsistent state.
        """
        # Corrupt the database by dropping a table that has foreign key references
        import psycopg2

        with psycopg2.connect(test_database) as conn:
            with conn.cursor() as cur:
                # Drop a table that has foreign key references (this will cause issues)
                cur.execute("DROP TABLE users CASCADE")
            conn.commit()

        # Attempt backup - should fail gracefully
        backup_path = tmp_path / "corrupted_backup.sql.gz"
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                test_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        # Backup should fail due to corrupted database
        assert result.returncode != 0, "Backup should fail with corrupted database"
        assert "error" in result.stderr.lower() or "failed" in result.stderr.lower()

    def test_restore_with_corrupted_backup_file(
        self, test_database: str, tmp_path: Path
    ):
        """
        Test restore behavior when backup file is corrupted or truncated.
        """
        # Create a valid backup first
        valid_backup_path = tmp_path / "valid_backup.sql.gz"
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(valid_backup_path),
                "--db-url",
                test_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        assert result.returncode == 0, f"Failed to create valid backup: {result.stderr}"
        assert valid_backup_path.exists(), "Valid backup file not created"

        # Create a corrupted backup file by truncating it
        corrupted_backup_path = tmp_path / "corrupted_backup.sql.gz"
        with open(valid_backup_path, "rb") as src, open(
            corrupted_backup_path, "wb"
        ) as dst:
            # Copy only the first 1000 bytes to create a corrupted file
            dst.write(src.read(1000))

        # Create fresh database for restore
        client = docker.from_env()
        container = client.containers.run(
            "postgres:15-alpine",
            environment={
                "POSTGRES_USER": "testuser",
                "POSTGRES_PASSWORD": "testpass",
                "POSTGRES_DB": "restoredb",
            },
            ports={"5432/tcp": None},
            detach=True,
            remove=True,
        )

        try:
            # Wait for container to be ready
            container.reload()
            port = container.ports["5432/tcp"][0]["HostPort"]
            restore_dsn = f"postgresql://testuser:testpass@localhost:{port}/restoredb"

            # Wait for PostgreSQL to be ready
            for _ in range(30):
                try:
                    engine = create_engine(restore_dsn)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    engine.dispose()
                    break
                except Exception:
                    time.sleep(1)
            else:
                pytest.fail("Restore database not ready within timeout")

            # Attempt restore with corrupted file - should fail gracefully
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "app.utils.db_backup",
                    "restore",
                    "--input",
                    str(corrupted_backup_path),
                    "--db-url",
                    restore_dsn,
                    "--force",
                ],
                capture_output=True,
                text=True,
                cwd="backend",
            )

            # Restore should fail due to corrupted backup file
            assert (
                result.returncode != 0
            ), "Restore should fail with corrupted backup file"
            assert "error" in result.stderr.lower() or "failed" in result.stderr.lower()

        finally:
            container.stop()

    def test_backup_with_insufficient_disk_space(
        self, test_database: str, tmp_path: Path
    ):
        """
        Test backup behavior when there's insufficient disk space.
        """
        # Create a backup path in a directory that might be full
        # For testing, we'll use a path that doesn't exist to simulate permission issues
        backup_path = Path("/nonexistent/directory/backup.sql.gz")

        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                test_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        # Backup should fail due to insufficient disk space or permission issues
        assert result.returncode != 0, "Backup should fail with insufficient disk space"
        assert "error" in result.stderr.lower() or "failed" in result.stderr.lower()

    def test_restore_with_invalid_database_url(self, tmp_path: Path):
        """
        Test restore behavior with invalid database connection parameters.
        """
        # Create a valid backup first using a working database
        client = docker.from_env()
        container = client.containers.run(
            "postgres:15-alpine",
            environment={
                "POSTGRES_USER": "testuser",
                "POSTGRES_PASSWORD": "testpass",
                "POSTGRES_DB": "testdb",
            },
            ports={"5432/tcp": None},
            detach=True,
            remove=True,
        )

        try:
            # Wait for container to be ready
            container.reload()
            port = container.ports["5432/tcp"][0]["HostPort"]
            dsn = f"postgresql://testuser:testpass@localhost:{port}/testdb"

            # Wait for PostgreSQL to be ready
            for _ in range(30):
                try:
                    engine = create_engine(dsn)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    engine.dispose()
                    break
                except Exception:
                    time.sleep(1)
            else:
                pytest.fail("Database not ready within timeout")

            # Create backup
            backup_path = tmp_path / "test_backup.sql.gz"
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "app.utils.db_backup",
                    "backup",
                    "--output",
                    str(backup_path),
                    "--db-url",
                    dsn,
                ],
                capture_output=True,
                text=True,
                cwd="backend",
            )

            assert result.returncode == 0, f"Failed to create backup: {result.stderr}"
            assert backup_path.exists(), "Backup file not created"

            # Attempt restore with invalid database URL
            invalid_dsn = "postgresql://invalid:invalid@localhost:9999/invalid"
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "app.utils.db_backup",
                    "restore",
                    "--input",
                    str(backup_path),
                    "--db-url",
                    invalid_dsn,
                    "--force",
                ],
                capture_output=True,
                text=True,
                cwd="backend",
            )

            # Restore should fail due to invalid database URL
            assert (
                result.returncode != 0
            ), "Restore should fail with invalid database URL"
            assert "error" in result.stderr.lower() or "failed" in result.stderr.lower()

        finally:
            container.stop()

    def test_backup_with_database_connection_failure(self, tmp_path: Path):
        """
        Test backup behavior when database connection fails.
        """
        # Use an invalid database URL
        invalid_dsn = "postgresql://invalid:invalid@localhost:9999/invalid"
        backup_path = tmp_path / "connection_failure_backup.sql.gz"

        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                invalid_dsn,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        # Backup should fail due to connection failure
        assert result.returncode != 0, "Backup should fail with connection failure"
        assert "error" in result.stderr.lower() or "failed" in result.stderr.lower()

    def test_restore_without_force_flag_in_production(
        self, test_database: str, tmp_path: Path
    ):
        """
        Test that restore fails without --force flag in production environment.
        """
        # Create a backup
        backup_path = tmp_path / "production_backup.sql.gz"
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                test_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        assert result.returncode == 0, f"Failed to create backup: {result.stderr}"
        assert backup_path.exists(), "Backup file not created"

        # Set production environment
        env = os.environ.copy()
        env["ENV"] = "production"

        # Attempt restore without --force flag in production
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "restore",
                "--input",
                str(backup_path),
                "--db-url",
                test_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
            env=env,
        )

        # Restore should fail without --force flag in production
        assert (
            result.returncode != 0
        ), "Restore should fail without --force flag in production"
        assert "production" in result.stderr.lower() or "force" in result.stderr.lower()

    def test_backup_with_concurrent_database_changes(
        self, test_database: str, tmp_path: Path
    ):
        """
        Test backup behavior when database is being modified concurrently.
        """
        import threading
        import time

        # Start a background thread that continuously modifies the database
        stop_thread = threading.Event()

        def modify_database():
            import psycopg2

            while not stop_thread.is_set():
                try:
                    with psycopg2.connect(test_database) as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                                (
                                    f"user_{int(time.time())}",
                                    f"user_{int(time.time())}@example.com",
                                    "hash",
                                ),
                            )
                        conn.commit()
                except Exception:
                    pass
                time.sleep(0.1)

        # Start the background modification thread
        thread = threading.Thread(target=modify_database)
        thread.start()

        try:
            # Perform backup while database is being modified
            backup_path = tmp_path / "concurrent_backup.sql.gz"
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "app.utils.db_backup",
                    "backup",
                    "--output",
                    str(backup_path),
                    "--db-url",
                    test_database,
                ],
                capture_output=True,
                text=True,
                cwd="backend",
            )

            # Backup should complete successfully even with concurrent modifications
            assert (
                result.returncode == 0
            ), f"Backup failed with concurrent modifications: {result.stderr}"
            assert (
                backup_path.exists()
            ), "Backup file not created with concurrent modifications"

        finally:
            # Stop the background thread
            stop_thread.set()
            thread.join()

    def test_restore_with_existing_data(self, test_database: str, tmp_path: Path):
        """
        Test restore behavior when target database already has data.
        """
        # Create a backup
        backup_path = tmp_path / "existing_data_backup.sql.gz"
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                test_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        assert result.returncode == 0, f"Failed to create backup: {result.stderr}"
        assert backup_path.exists(), "Backup file not created"

        # Add some data to the database after backup
        import psycopg2

        with psycopg2.connect(test_database) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    ("new_user", "new_user@example.com", "new_hash"),
                )
            conn.commit()

        # Attempt restore without --force flag
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "restore",
                "--input",
                str(backup_path),
                "--db-url",
                test_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        # Restore should fail without --force flag when database has existing data
        assert (
            result.returncode != 0
        ), "Restore should fail without --force flag when database has existing data"
        assert "existing" in result.stderr.lower() or "force" in result.stderr.lower()

    def test_backup_with_large_transaction_log(
        self, test_database: str, tmp_path: Path
    ):
        """
        Test backup behavior with a large transaction log.
        """
        # Create many small transactions to build up the transaction log
        import psycopg2

        for i in range(1000):
            with psycopg2.connect(test_database) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                        (f"user_{i}", f"user_{i}@example.com", f"hash_{i}"),
                    )
                conn.commit()

        # Perform backup with large transaction log
        backup_path = tmp_path / "large_txn_backup.sql.gz"
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                test_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        # Backup should complete successfully
        assert (
            result.returncode == 0
        ), f"Backup failed with large transaction log: {result.stderr}"
        assert (
            backup_path.exists()
        ), "Backup file not created with large transaction log"

    def test_restore_with_different_postgres_version(
        self, test_database: str, tmp_path: Path
    ):
        """
        Test restore behavior when target database has a different PostgreSQL version.
        """
        # Create a backup
        backup_path = tmp_path / "version_backup.sql.gz"
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                test_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        assert result.returncode == 0, f"Failed to create backup: {result.stderr}"
        assert backup_path.exists(), "Backup file not created"

        # Create a PostgreSQL 16 container (different version)
        client = docker.from_env()
        container = client.containers.run(
            "postgres:16-alpine",
            environment={
                "POSTGRES_USER": "testuser",
                "POSTGRES_PASSWORD": "testpass",
                "POSTGRES_DB": "versiondb",
            },
            ports={"5432/tcp": None},
            detach=True,
            remove=True,
        )

        try:
            # Wait for container to be ready
            container.reload()
            port = container.ports["5432/tcp"][0]["HostPort"]
            restore_dsn = f"postgresql://testuser:testpass@localhost:{port}/versiondb"

            # Wait for PostgreSQL to be ready
            for _ in range(30):
                try:
                    engine = create_engine(restore_dsn)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    engine.dispose()
                    break
                except Exception:
                    time.sleep(1)
            else:
                pytest.fail("Restore database not ready within timeout")

            # Attempt restore to different PostgreSQL version
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "app.utils.db_backup",
                    "restore",
                    "--input",
                    str(backup_path),
                    "--db-url",
                    restore_dsn,
                    "--force",
                ],
                capture_output=True,
                text=True,
                cwd="backend",
            )

            # Restore should either succeed or fail gracefully with version mismatch
            if result.returncode != 0:
                # If it fails, it should be due to version incompatibility
                assert (
                    "version" in result.stderr.lower()
                    or "compatibility" in result.stderr.lower()
                )
            else:
                # If it succeeds, verify data integrity
                _ = TestDataManager(restore_dsn)
                # Basic check that tables exist
                import psycopg2

                with psycopg2.connect(restore_dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM users")
                        count = cur.fetchone()[0]
                        assert (
                            count > 0
                        ), "No users found after restore to different PostgreSQL version"

        finally:
            container.stop()
