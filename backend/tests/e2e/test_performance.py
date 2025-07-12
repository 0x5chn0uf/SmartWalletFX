"""Performance tests for backup and restore functionality.

These tests validate that backup and restore operations meet performance requirements
and monitor resource usage during operations.
"""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import AsyncGenerator

import docker
import psutil
import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text

from tests.utils.test_data_manager import TestDataManager

POSTGRES_URL_TEMPLATE = "postgresql://testuser:testpass@localhost:{port}/{db}"


@pytest.fixture(scope="module")
def postgres_large_container():
    """
    Spins up the postgres-large container (port 5435), yields DB URL, and tears down after tests.
    Assumes docker-compose.e2e.yml is up.
    """
    port = 5435
    db = "largedb"
    url = POSTGRES_URL_TEMPLATE.format(port=port, db=db)
    # Wait for container to be ready
    for _ in range(60):
        try:
            import psycopg2

            with psycopg2.connect(url):
                return url
        except Exception:
            time.sleep(2)
    pytest.skip("Postgres large container not ready on port 5435")


@pytest.mark.performance
class TestBackupPerformance:
    """Performance benchmarks for backup operations."""

    @pytest_asyncio.fixture
    async def large_database(self) -> AsyncGenerator[str, None]:
        """Set up a large database for performance testing."""
        client = docker.from_env()

        # Start PostgreSQL container with large dataset
        container = client.containers.run(
            "postgres:15-alpine",
            environment={
                "POSTGRES_USER": "testuser",
                "POSTGRES_PASSWORD": "testpass",
                "POSTGRES_DB": "perfdb",
            },
            ports={"5432/tcp": None},
            detach=True,
            remove=True,
        )

        try:
            # Wait for container to be ready
            container.reload()
            port = container.ports["5432/tcp"][0]["HostPort"]
            dsn = f"postgresql://testuser:testpass@localhost:{port}/perfdb"

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

            # Load large dataset
            TestDataManager.generate_realistic_schema(dsn, size="large")
            TestDataManager.populate_test_data(dsn, volume="large")

            yield dsn

        finally:
            container.stop()

    def test_backup_performance_1gb_requirement(
        self, large_database: str, tmp_path: Path
    ):
        """
        Ensure backup completes within 30s for 1GB dataset.
        This test validates the performance requirement from Task 8.
        """
        backup_path = tmp_path / "performance_backup.sql.gz"

        # Measure backup time
        start_time = time.perf_counter()

        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                large_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        backup_time = time.perf_counter() - start_time

        # Verify backup completed successfully
        assert result.returncode == 0, f"Backup failed: {result.stderr}"
        assert backup_path.exists(), "Backup file was not created"

        # Check performance requirement: < 30s for 1GB
        assert (
            backup_time < 30.0
        ), f"Backup took {backup_time:.2f}s, exceeds 30s requirement"

        # Log performance metrics
        backup_size = backup_path.stat().st_size
        print("\nBackup Performance Metrics:")
        print(f"  Time: {backup_time:.2f}s")
        print(f"  Size: {backup_size / (1024*1024):.2f} MB")
        print(f"  Rate: {backup_size / (1024*1024) / backup_time:.2f} MB/s")

    def test_backup_memory_usage(self, large_database: str, tmp_path: Path):
        """
        Monitor memory usage during backup operations.
        Ensures backup doesn't consume excessive memory.
        """
        backup_path = tmp_path / "memory_backup.sql.gz"

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Start backup
        start_time = time.perf_counter()
        backup_process = subprocess.Popen(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                large_database,
            ],
            cwd="backend",
        )

        # Monitor memory usage during backup
        max_memory = initial_memory
        while backup_process.poll() is None:
            current_memory = process.memory_info().rss
            max_memory = max(max_memory, current_memory)
            time.sleep(0.1)

        backup_time = time.perf_counter() - start_time

        # Verify backup completed successfully
        assert backup_process.returncode == 0, "Backup process failed"
        assert backup_path.exists(), "Backup file was not created"

        # Check memory usage (should not exceed 500MB)
        memory_increase = max_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)

        assert (
            memory_increase_mb < 500
        ), f"Memory usage increased by {memory_increase_mb:.2f}MB, exceeds 500MB limit"

        print("\nMemory Usage Metrics:")
        print(f"  Initial: {initial_memory / (1024*1024):.2f} MB")
        print(f"  Peak: {max_memory / (1024*1024):.2f} MB")
        print(f"  Increase: {memory_increase_mb:.2f} MB")
        print(f"  Duration: {backup_time:.2f}s")

    def test_backup_cpu_usage(self, large_database: str, tmp_path: Path):
        """
        Monitor CPU usage during backup operations.
        Ensures backup doesn't consume excessive CPU.
        """
        backup_path = tmp_path / "cpu_backup.sql.gz"

        # Start backup
        start_time = time.perf_counter()
        backup_process = subprocess.Popen(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                large_database,
            ],
            cwd="backend",
        )

        # Monitor CPU usage during backup
        cpu_samples = []
        while backup_process.poll() is None:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_samples.append(cpu_percent)
            time.sleep(0.1)

        backup_time = time.perf_counter() - start_time

        # Verify backup completed successfully
        assert backup_process.returncode == 0, "Backup process failed"
        assert backup_path.exists(), "Backup file was not created"

        # Calculate CPU metrics
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        max_cpu = max(cpu_samples) if cpu_samples else 0

        # Check CPU usage (average should be reasonable)
        assert avg_cpu < 80, f"Average CPU usage {avg_cpu:.1f}% exceeds 80% limit"

        print("\nCPU Usage Metrics:")
        print(f"  Average: {avg_cpu:.1f}%")
        print(f"  Peak: {max_cpu:.1f}%")
        print(f"  Duration: {backup_time:.2f}s")

    def test_concurrent_backups(self, large_database: str, tmp_path: Path):
        """
        Test multiple concurrent backup operations.
        Ensures the system can handle concurrent backup requests.
        """
        backup_paths = [tmp_path / f"concurrent_backup_{i}.sql.gz" for i in range(3)]

        # Start multiple backup processes concurrently
        processes = []
        start_time = time.perf_counter()

        for _, backup_path in enumerate(backup_paths):
            process = subprocess.Popen(
                [
                    "python",
                    "-m",
                    "app.utils.db_backup",
                    "backup",
                    "--output",
                    str(backup_path),
                    "--db-url",
                    large_database,
                ],
                cwd="backend",
            )
            processes.append((process, backup_path))

        # Wait for all processes to complete
        for process, backup_path in processes:
            process.wait()
            assert process.returncode == 0, f"Concurrent backup failed: {backup_path}"
            assert (
                backup_path.exists()
            ), f"Concurrent backup file not created: {backup_path}"

        total_time = time.perf_counter() - start_time

        # All backups should complete successfully
        print("\nConcurrent Backup Metrics:")
        print(f"  Number of backups: {len(backup_paths)}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average time per backup: {total_time / len(backup_paths):.2f}s")

    def test_backup_with_compression(self, large_database: str, tmp_path: Path):
        """
        Test backup performance with different compression levels.
        Validates that compression doesn't significantly impact performance.
        """
        # Test with compression (default)
        compressed_path = tmp_path / "compressed_backup.sql.gz"
        start_time = time.perf_counter()

        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(compressed_path),
                "--db-url",
                large_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        compressed_time = time.perf_counter() - start_time

        assert result.returncode == 0, f"Compressed backup failed: {result.stderr}"
        assert compressed_path.exists(), "Compressed backup file not created"

        # Test without compression
        uncompressed_path = tmp_path / "uncompressed_backup.sql"
        start_time = time.perf_counter()

        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(uncompressed_path),
                "--db-url",
                large_database,
                "--no-compress",
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        uncompressed_time = time.perf_counter() - start_time

        assert result.returncode == 0, f"Uncompressed backup failed: {result.stderr}"
        assert uncompressed_path.exists(), "Uncompressed backup file not created"

        # Compare file sizes and times
        compressed_size = compressed_path.stat().st_size
        uncompressed_size = uncompressed_path.stat().st_size
        compression_ratio = (1 - compressed_size / uncompressed_size) * 100

        print("\nCompression Performance Metrics:")
        print(f"  Compressed time: {compressed_time:.2f}s")
        print(f"  Uncompressed time: {uncompressed_time:.2f}s")
        print(f"  Time difference: {abs(compressed_time - uncompressed_time):.2f}s")
        print(f"  Compressed size: {compressed_size / (1024*1024):.2f} MB")
        print(f"  Uncompressed size: {uncompressed_size / (1024*1024):.2f} MB")
        print(f"  Compression ratio: {compression_ratio:.1f}%")

        # Compression should not add more than 20% to backup time
        time_increase = (compressed_time - uncompressed_time) / uncompressed_time * 100
        assert (
            time_increase < 20
        ), f"Compression adds {time_increase:.1f}% overhead, exceeds 20% limit"


@pytest.mark.performance
class TestRestorePerformance:
    """Performance benchmarks for restore operations."""

    @pytest_asyncio.fixture
    async def backup_file(
        self, large_database: str, tmp_path: Path
    ) -> AsyncGenerator[Path, None]:
        """Create a backup file for restore testing."""
        backup_path = tmp_path / "restore_test_backup.sql.gz"

        # Create backup
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                large_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        assert (
            result.returncode == 0
        ), f"Failed to create backup for restore test: {result.stderr}"
        assert backup_path.exists(), "Backup file not created for restore test"

        yield backup_path

    def test_restore_performance_1gb_requirement(
        self, backup_file: Path, tmp_path: Path
    ):
        """
        Ensure restore completes within 60s for 1GB dataset.
        This test validates the restore performance requirement.
        """
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

            # Measure restore time
            start_time = time.perf_counter()

            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "app.utils.db_backup",
                    "restore",
                    "--input",
                    str(backup_file),
                    "--db-url",
                    restore_dsn,
                    "--force",
                ],
                capture_output=True,
                text=True,
                cwd="backend",
            )

            restore_time = time.perf_counter() - start_time

            # Verify restore completed successfully
            assert result.returncode == 0, f"Restore failed: {result.stderr}"

            # Check performance requirement: < 60s for 1GB
            assert (
                restore_time < 60.0
            ), f"Restore took {restore_time:.2f}s, exceeds 60s requirement"

            print("\nRestore Performance Metrics:")
            print(f"  Time: {restore_time:.2f}s")
            print(f"  Backup size: {backup_file.stat().st_size / (1024*1024):.2f} MB")

        finally:
            container.stop()

    def test_restore_memory_usage(self, backup_file: Path, tmp_path: Path):
        """
        Monitor memory usage during restore operations.
        Ensures restore doesn't consume excessive memory.
        """
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

            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss

            # Start restore
            start_time = time.perf_counter()
            restore_process = subprocess.Popen(
                [
                    "python",
                    "-m",
                    "app.utils.db_backup",
                    "restore",
                    "--input",
                    str(backup_file),
                    "--db-url",
                    restore_dsn,
                    "--force",
                ],
                cwd="backend",
            )

            # Monitor memory usage during restore
            max_memory = initial_memory
            while restore_process.poll() is None:
                current_memory = process.memory_info().rss
                max_memory = max(max_memory, current_memory)
                time.sleep(0.1)

            restore_time = time.perf_counter() - start_time

            # Verify restore completed successfully
            assert restore_process.returncode == 0, "Restore process failed"

            # Check memory usage (should not exceed 1GB)
            memory_increase = max_memory - initial_memory
            memory_increase_mb = memory_increase / (1024 * 1024)

            assert (
                memory_increase_mb < 1024
            ), f"Memory usage increased by {memory_increase_mb:.2f}MB, exceeds 1GB limit"

            print("\nRestore Memory Usage Metrics:")
            print(f"  Initial: {initial_memory / (1024*1024):.2f} MB")
            print(f"  Peak: {max_memory / (1024*1024):.2f} MB")
            print(f"  Increase: {memory_increase_mb:.2f} MB")
            print(f"  Duration: {restore_time:.2f}s")

        finally:
            container.stop()

    def test_restore_data_integrity(self, backup_file: Path, tmp_path: Path):
        """
        Test that restored data maintains integrity.
        Validates that restore operation preserves all data correctly.
        """
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

            # Perform restore
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "app.utils.db_backup",
                    "restore",
                    "--input",
                    str(backup_file),
                    "--db-url",
                    restore_dsn,
                    "--force",
                ],
                capture_output=True,
                text=True,
                cwd="backend",
            )

            assert result.returncode == 0, f"Restore failed: {result.stderr}"

            # Validate data integrity using TestDataManager
            TestDataManager.generate_realistic_schema(restore_dsn, size="large")
            TestDataManager.populate_test_data(restore_dsn, volume="large")

            # Check that all tables exist and have data
            import psycopg2

            with psycopg2.connect(restore_dsn) as conn:
                with conn.cursor() as cur:
                    # Check table counts
                    tables = [
                        "users",
                        "wallets",
                        "transactions",
                        "token_balances",
                        "portfolio_snapshots",
                    ]
                    for table in tables:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cur.fetchone()[0]
                        assert count > 0, f"Table {table} has no data after restore"
                        print(f"  {table}: {count} rows")

            print("\nRestore Data Integrity: All tables restored successfully")

        finally:
            container.stop()


@pytest.mark.performance
class TestSystemPerformance:
    """System-wide performance tests."""

    def test_backup_restore_cycle_performance(
        self, large_database: str, tmp_path: Path
    ):
        """
        Test complete backup-restore cycle performance.
        Validates end-to-end performance of the backup/restore workflow.
        """
        backup_path = tmp_path / "cycle_backup.sql.gz"

        # Measure backup time
        backup_start = time.perf_counter()
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                large_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        backup_time = time.perf_counter() - backup_start
        assert result.returncode == 0, f"Backup failed: {result.stderr}"
        assert backup_path.exists(), "Backup file not created"

        # Create fresh database for restore
        client = docker.from_env()
        container = client.containers.run(
            "postgres:15-alpine",
            environment={
                "POSTGRES_USER": "testuser",
                "POSTGRES_PASSWORD": "testpass",
                "POSTGRES_DB": "cycledb",
            },
            ports={"5432/tcp": None},
            detach=True,
            remove=True,
        )

        try:
            # Wait for container to be ready
            container.reload()
            port = container.ports["5432/tcp"][0]["HostPort"]
            restore_dsn = f"postgresql://testuser:testpass@localhost:{port}/cycledb"

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

            # Measure restore time
            restore_start = time.perf_counter()
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

            restore_time = time.perf_counter() - restore_start
            assert result.returncode == 0, f"Restore failed: {result.stderr}"

            # Calculate total cycle time
            total_time = backup_time + restore_time

            # Performance requirements
            assert (
                backup_time < 30.0
            ), f"Backup took {backup_time:.2f}s, exceeds 30s requirement"
            assert (
                restore_time < 60.0
            ), f"Restore took {restore_time:.2f}s, exceeds 60s requirement"
            assert (
                total_time < 90.0
            ), f"Total cycle took {total_time:.2f}s, exceeds 90s requirement"

            print("\nBackup-Restore Cycle Performance:")
            print(f"  Backup time: {backup_time:.2f}s")
            print(f"  Restore time: {restore_time:.2f}s")
            print(f"  Total cycle time: {total_time:.2f}s")
            print(f"  Backup size: {backup_path.stat().st_size / (1024*1024):.2f} MB")

        finally:
            container.stop()

    def test_resource_cleanup_after_operations(
        self, large_database: str, tmp_path: Path
    ):
        """
        Test that resources are properly cleaned up after backup/restore operations.
        Ensures no memory leaks or resource exhaustion.
        """
        backup_path = tmp_path / "cleanup_backup.sql.gz"

        # Get initial resource usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        initial_open_files = len(process.open_files())

        # Perform backup
        result = subprocess.run(
            [
                "python",
                "-m",
                "app.utils.db_backup",
                "backup",
                "--output",
                str(backup_path),
                "--db-url",
                large_database,
            ],
            capture_output=True,
            text=True,
            cwd="backend",
        )

        assert result.returncode == 0, f"Backup failed: {result.stderr}"

        # Wait a moment for cleanup
        time.sleep(1)

        # Check resource usage after backup
        post_backup_memory = process.memory_info().rss
        post_backup_files = len(process.open_files())

        # Memory should be close to initial (within 10%)
        memory_increase = (post_backup_memory - initial_memory) / initial_memory * 100
        assert (
            memory_increase < 10
        ), f"Memory usage increased by {memory_increase:.1f}% after backup"

        # File handles should be cleaned up
        file_increase = post_backup_files - initial_open_files
        assert (
            file_increase <= 5
        ), f"Open files increased by {file_increase} after backup"

        print("\nResource Cleanup Metrics:")
        print(f"  Memory increase: {memory_increase:.1f}%")
        print(f"  File handle increase: {file_increase}")
        print(f"  Initial memory: {initial_memory / (1024*1024):.2f} MB")
        print(f"  Post-backup memory: {post_backup_memory / (1024*1024):.2f} MB")
