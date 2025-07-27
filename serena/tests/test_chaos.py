"""
Chaos tests for the Memory Bridge system.
Tests concurrent operations, error recovery, and system resilience.
"""

import concurrent.futures
import os
import random
import sqlite3
import tempfile
import time

import pytest

from serena.infrastructure.database import init_database
from serena.infrastructure.embeddings import EmbeddingGenerator as EmbeddingManager
from serena.services.memory_impl import Memory


class TestMemoryChaos:
    """Chaos tests for system resilience and concurrent safety."""

    @pytest.fixture
    def chaos_db(self):
        """Create a database for chaos testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        init_database(db_path)

        # Pre-populate with some data for chaos testing
        memory = Memory(db_path=db_path)
        for i in range(100):
            task_id = f"chaos-task-{i:03d}"
            content = f"# Chaos Test Task {i}\n\nContent for chaos testing task {i}."
            memory.upsert(task_id, content, title=f"Chaos Task {i}")

        yield db_path

        # Cleanup
        try:
            os.unlink(db_path)
            for suffix in ["-wal", "-shm"]:
                wal_path = db_path + suffix
                if os.path.exists(wal_path):
                    os.unlink(wal_path)
        except OSError:
            pass

    @pytest.mark.chaos
    def test_concurrent_writers_and_readers(self, chaos_db):
        """Test system stability with concurrent writers and readers."""

        def writer_worker(worker_id, num_operations=50):
            """Worker that performs write operations."""
            memory = Memory(db_path=chaos_db)
            operations = 0
            errors = []

            for i in range(num_operations):
                try:
                    task_id = f"writer-{worker_id}-task-{i:03d}"
                    content = f"# Writer {worker_id} Task {i}\n\nContent from writer {worker_id}, operation {i}."
                    success = memory.upsert(
                        task_id, content, title=f"Writer {worker_id} Task {i}"
                    )

                    if success:
                        operations += 1
                    else:
                        errors.append(f"Upsert failed for {task_id}")

                    # Small random delay to create realistic contention
                    time.sleep(random.uniform(0.001, 0.01))

                except Exception as e:
                    errors.append(f"Writer {worker_id} operation {i}: {str(e)}")

            return operations, errors

        def reader_worker(worker_id, num_operations=100):
            """Worker that performs read operations."""
            memory = Memory(db_path=chaos_db)
            operations = 0
            errors = []

            for i in range(num_operations):
                try:
                    # Mix of gets and searches
                    if i % 3 == 0:
                        # Search operation
                        query = f"chaos test task {i % 10}"
                        results = memory.search(query, k=5)
                        operations += 1
                    else:
                        # Get operation
                        task_id = f"chaos-task-{i % 100:03d}"
                        result = memory.get(task_id)
                        if result is not None:
                            operations += 1
                        else:
                            errors.append(f"Task {task_id} not found")

                    # Small random delay
                    time.sleep(random.uniform(0.001, 0.005))

                except Exception as e:
                    errors.append(f"Reader {worker_id} operation {i}: {str(e)}")

            return operations, errors

        # Test with 4 concurrent writers and 4 concurrent readers
        num_writers = 4
        num_readers = 4

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=num_writers + num_readers
        ) as executor:
            # Submit writer tasks
            writer_futures = [
                executor.submit(writer_worker, i, 25) for i in range(num_writers)
            ]

            # Submit reader tasks
            reader_futures = [
                executor.submit(reader_worker, i, 50) for i in range(num_readers)
            ]

            # Collect results
            writer_results = []
            reader_results = []

            for future in concurrent.futures.as_completed(writer_futures):
                operations, errors = future.result()
                writer_results.append((operations, errors))

            for future in concurrent.futures.as_completed(reader_futures):
                operations, errors = future.result()
                reader_results.append((operations, errors))

        # Analyze results
        total_write_ops = sum(ops for ops, errors in writer_results)
        total_write_errors = sum(len(errors) for ops, errors in writer_results)

        total_read_ops = sum(ops for ops, errors in reader_results)
        total_read_errors = sum(len(errors) for ops, errors in reader_results)

        # Should complete most operations successfully
        write_success_rate = (
            total_write_ops / (total_write_ops + total_write_errors)
            if (total_write_ops + total_write_errors) > 0
            else 0
        )
        read_success_rate = (
            total_read_ops / (total_read_ops + total_read_errors)
            if (total_read_ops + total_read_errors) > 0
            else 0
        )

        assert (
            write_success_rate > 0.95
        ), f"Write success rate {write_success_rate:.2%} too low"
        assert (
            read_success_rate > 0.95
        ), f"Read success rate {read_success_rate:.2%} too low"

        # Should not encounter SQLite locking errors
        all_errors = []
        for ops, errors in writer_results + reader_results:
            all_errors.extend(errors)

        locking_errors = [
            e for e in all_errors if "database is locked" in str(e).lower()
        ]
        assert (
            len(locking_errors) == 0
        ), f"Encountered {len(locking_errors)} SQLite locking errors"

        print(f"Concurrent operations completed:")
        print(f"  Writers: {total_write_ops} operations, {total_write_errors} errors")
        print(f"  Readers: {total_read_ops} operations, {total_read_errors} errors")
        print(f"  Write success rate: {write_success_rate:.2%}")
        print(f"  Read success rate: {read_success_rate:.2%}")

    @pytest.mark.chaos
    def test_database_corruption_recovery(self, chaos_db):
        """Test system behavior when database files are corrupted."""
        memory = Memory(db_path=chaos_db)

        # Verify system works initially
        result = memory.get("chaos-task-001")
        assert result is not None

        # Simulate WAL file corruption by writing garbage
        wal_path = chaos_db + "-wal"
        shm_path = chaos_db + "-shm"

        # Force WAL creation by performing a write
        memory.upsert("corruption-test", "Test content", title="Corruption Test")

        # Check if WAL file exists and corrupt it
        if os.path.exists(wal_path):
            with open(wal_path, "wb") as f:
                f.write(b"CORRUPTED_DATA" * 1000)

            # System should handle corruption gracefully
            try:
                # This might fail, but shouldn't crash the process
                memory.get("chaos-task-002")
            except sqlite3.DatabaseError:
                # Expected behavior - database detects corruption
                pass

            # Remove corrupted WAL to allow recovery
            os.unlink(wal_path)
            if os.path.exists(shm_path):
                os.unlink(shm_path)

            # Create new Memory instance (simulates restart)
            recovered_memory = Memory(db_path=chaos_db)

            # Should be able to access data again
            recovered_result = recovered_memory.get("chaos-task-001")
            assert recovered_result is not None, "Failed to recover after corruption"

    @pytest.mark.chaos
    def test_rapid_cache_thrashing(self, chaos_db):
        """Test cache behavior under rapid access to many different items."""
        # Small cache to force thrashing
        memory = Memory(db_path=chaos_db, cache_size=10)

        def cache_thrasher(worker_id, duration_seconds=3):
            """Worker that rapidly accesses many different cache items."""
            start_time = time.time()
            operations = 0
            errors = []

            while time.time() - start_time < duration_seconds:
                try:
                    # Access random tasks to force cache eviction
                    task_id = f"chaos-task-{random.randint(0, 99):03d}"
                    result = memory.get(task_id)

                    if result is not None:
                        operations += 1
                    else:
                        errors.append(f"Task {task_id} not found")

                except Exception as e:
                    errors.append(f"Worker {worker_id}: {str(e)}")

            return operations, errors

        # Multiple workers thrashing the cache simultaneously
        num_workers = 6

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(cache_thrasher, i) for i in range(num_workers)]

            results = []
            for future in concurrent.futures.as_completed(futures):
                operations, errors = future.result()
                results.append((operations, errors))

        # Should handle cache thrashing without errors
        total_operations = sum(ops for ops, errors in results)
        total_errors = sum(len(errors) for ops, errors in results)

        error_rate = total_errors / total_operations if total_operations > 0 else 0
        assert (
            error_rate < 0.05
        ), f"Error rate {error_rate:.2%} too high during cache thrashing"

        print(
            f"Cache thrashing test: {total_operations} operations, {total_errors} errors"
        )

    @pytest.mark.chaos
    def test_memory_leak_under_stress(self, chaos_db):
        """Test for memory leaks during extended operation."""
        import gc

        import psutil

        memory = Memory(db_path=chaos_db)
        process = psutil.Process()

        # Get baseline memory usage
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many operations that could leak memory
        for cycle in range(10):
            # Simulate a work cycle
            for i in range(100):
                # Mix of operations
                if i % 4 == 0:
                    # Upsert new content
                    task_id = f"leak-test-{cycle}-{i}"
                    content = (
                        f"# Leak Test\n\nCycle {cycle}, iteration {i}. " + "x" * 1000
                    )
                    memory.upsert(task_id, content, title=f"Leak Test {cycle}-{i}")
                elif i % 4 == 1:
                    # Search operations
                    memory.search(f"leak test cycle {cycle % 5}", k=10)
                elif i % 4 == 2:
                    # Get operations
                    task_id = f"chaos-task-{i % 100:03d}"
                    memory.get(task_id)
                else:
                    # Health check
                    memory.health()

            # Check memory periodically
            if cycle % 3 == 0:
                gc.collect()
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_growth = current_memory - baseline_memory

                # Memory growth should be reasonable (under 50MB per cycle)
                assert memory_growth < 50 * (
                    cycle // 3 + 1
                ), f"Excessive memory growth: {memory_growth:.2f}MB after cycle {cycle}"

        # Final memory check
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_growth = final_memory - baseline_memory

        # Total growth should be reasonable for the amount of work done
        assert (
            total_growth < 200
        ), f"Total memory growth {total_growth:.2f}MB indicates potential leak"

        print(
            f"Memory usage: {baseline_memory:.2f}MB -> {final_memory:.2f}MB (growth: {total_growth:.2f}MB)"
        )

    @pytest.mark.chaos
    def test_filesystem_permission_errors(self, chaos_db):
        """Test behavior when filesystem permissions change."""
        memory = Memory(db_path=chaos_db)

        # Verify normal operation
        result = memory.get("chaos-task-001")
        assert result is not None

        # Make database read-only
        original_mode = os.stat(chaos_db).st_mode
        try:
            os.chmod(chaos_db, 0o444)  # Read-only

            # Read operations should still work
            result = memory.get("chaos-task-002")
            assert result is not None, "Read failed with read-only database"

            # Write operations should fail gracefully
            success = memory.upsert(
                "permission-test", "Test content", title="Permission Test"
            )
            assert not success, "Write unexpectedly succeeded with read-only database"

        finally:
            # Restore permissions
            os.chmod(chaos_db, original_mode)

        # Verify system recovers after permission restoration
        success = memory.upsert(
            "permission-recovered", "Recovered content", title="Permission Recovered"
        )
        assert success, "Failed to recover after permission restoration"

    @pytest.mark.chaos
    def test_embedding_model_failure_resilience(self, chaos_db):
        """Test system behavior when embedding model fails."""
        # This test simulates embedding failures by temporarily breaking the model
        memory = Memory(db_path=chaos_db)

        # Save original embedding method
        original_generate = EmbeddingManager.generate_embeddings

        # Mock a failing embedding generation
        def failing_embeddings(self, texts):
            if random.random() < 0.3:  # 30% failure rate
                raise Exception("Simulated embedding model failure")
            return original_generate(self, texts)

        # Patch the method
        EmbeddingManager.generate_embeddings = failing_embeddings

        try:
            operations = 0
            failures = 0

            # Perform multiple upsert operations
            for i in range(20):
                task_id = f"embedding-chaos-{i:03d}"
                content = f"# Embedding Chaos Test {i}\n\nContent that needs embedding."

                try:
                    success = memory.upsert(
                        task_id, content, title=f"Embedding Chaos {i}"
                    )
                    if success:
                        operations += 1
                    else:
                        failures += 1
                except Exception:
                    failures += 1

            # Should handle some failures gracefully
            success_rate = (
                operations / (operations + failures)
                if (operations + failures) > 0
                else 0
            )
            assert (
                success_rate > 0.5
            ), f"Success rate {success_rate:.2%} too low with embedding failures"

            # System should remain operational for searches (even without embeddings)
            results = memory.search("chaos test", k=5)
            # Results might be empty if no embeddings, but shouldn't crash
            assert isinstance(
                results, list
            ), "Search should return list even with embedding failures"

        finally:
            # Restore original method
            EmbeddingManager.generate_embeddings = original_generate

    @pytest.mark.chaos
    def test_database_connection_interruption(self, chaos_db):
        """Test recovery from database connection interruptions."""
        memory = Memory(db_path=chaos_db)

        # Verify normal operation
        result = memory.get("chaos-task-001")
        assert result is not None

        # Simulate connection interruption by moving the database file temporarily
        backup_path = chaos_db + ".backup"

        try:
            # Move database file
            os.rename(chaos_db, backup_path)

            # Operations should fail gracefully
            result = memory.get("chaos-task-002")
            assert result is None, "Get should fail with missing database"

            success = memory.upsert("connection-test", "Test", title="Connection Test")
            assert not success, "Upsert should fail with missing database"

        finally:
            # Restore database
            if os.path.exists(backup_path):
                os.rename(backup_path, chaos_db)

        # Create new Memory instance to simulate reconnection
        recovered_memory = Memory(db_path=chaos_db)

        # Should work again after reconnection
        result = recovered_memory.get("chaos-task-001")
        assert result is not None, "Failed to reconnect after database restoration"

        success = recovered_memory.upsert(
            "connection-recovered", "Recovered", title="Connection Recovered"
        )
        assert success, "Failed to write after database restoration"

    @pytest.mark.chaos
    def test_concurrent_database_checkpoints(self, chaos_db):
        """Test concurrent operations during WAL checkpoint operations."""
        memory = Memory(db_path=chaos_db)

        def checkpoint_worker():
            """Worker that performs periodic WAL checkpoints."""
            conn = sqlite3.connect(chaos_db)
            try:
                for _ in range(10):
                    time.sleep(0.1)
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    conn.commit()
            finally:
                conn.close()

        def operation_worker(worker_id):
            """Worker that performs normal operations during checkpoints."""
            operations = 0
            errors = []

            for i in range(50):
                try:
                    if i % 2 == 0:
                        task_id = f"checkpoint-test-{worker_id}-{i}"
                        success = memory.upsert(
                            task_id, f"Content {i}", title=f"Checkpoint Test {i}"
                        )
                        if success:
                            operations += 1
                    else:
                        result = memory.get(f"chaos-task-{i % 10:03d}")
                        if result is not None:
                            operations += 1

                    time.sleep(0.01)  # Small delay

                except Exception as e:
                    errors.append(str(e))

            return operations, errors

        # Run checkpoint worker alongside operation workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit checkpoint worker
            checkpoint_future = executor.submit(checkpoint_worker)

            # Submit operation workers
            operation_futures = [executor.submit(operation_worker, i) for i in range(3)]

            # Wait for completion
            checkpoint_future.result()  # Should complete without errors

            # Collect operation results
            results = []
            for future in concurrent.futures.as_completed(operation_futures):
                operations, errors = future.result()
                results.append((operations, errors))

        # Should complete most operations successfully despite checkpoints
        total_operations = sum(ops for ops, errors in results)
        total_errors = sum(len(errors) for ops, errors in results)

        success_rate = (
            total_operations / (total_operations + total_errors)
            if (total_operations + total_errors) > 0
            else 0
        )
        assert (
            success_rate > 0.9
        ), f"Success rate {success_rate:.2%} too low during checkpoints"

        print(f"Checkpoint test: {total_operations} operations, {total_errors} errors")


@pytest.mark.chaos
class TestMemoryExtremeConditions:
    """Tests for extreme operating conditions."""

    def test_very_large_content_handling(self, chaos_db):
        """Test handling of very large content files."""
        memory = Memory(db_path=chaos_db)

        # Test with content of various sizes
        sizes = [1_000, 10_000, 100_000, 500_000]  # Up to 500KB

        for size in sizes:
            task_id = f"large-content-{size}"
            content = f"# Large Content Test {size}\n\n" + "Large content test. " * (
                size // 20
            )

            start_time = time.time()
            success = memory.upsert(task_id, content, title=f"Large Content {size}")
            upsert_time = time.time() - start_time

            assert success, f"Failed to upsert content of size {size}"
            assert (
                upsert_time < 30
            ), f"Upsert took too long ({upsert_time:.2f}s) for size {size}"

            # Verify retrieval
            start_time = time.time()
            result = memory.get(task_id)
            get_time = time.time() - start_time

            assert result is not None, f"Failed to retrieve content of size {size}"
            assert (
                len(result["content"]) >= size * 0.9
            ), f"Content truncated for size {size}"
            assert get_time < 5, f"Get took too long ({get_time:.2f}s) for size {size}"

            print(f"Size {size}: upsert {upsert_time:.2f}s, get {get_time:.2f}s")

    def test_unicode_and_special_characters(self, chaos_db):
        """Test handling of Unicode and special characters in content."""
        memory = Memory(db_path=chaos_db)

        test_cases = [
            ("unicode-basic", "# Unicode Test\n\nHello 世界 🌍 émojis 🚀"),
            (
                "unicode-complex",
                "# Complex Unicode\n\n数据库 Ñoño莫斯科 🎭🎨🎪 \u200B\u2060",
            ),
            (
                "special-chars",
                "# Special Chars\n\n<>&\"' ${{variable}} [brackets] {braces}",
            ),
            ("sql-injection", "# SQL Test\n\n'; DROP TABLE archives; --"),
            (
                "markdown-chaos",
                "# Markdown\n\n```code``` **bold** *italic* > quote\n- list\n1. numbered",
            ),
        ]

        for task_id, content in test_cases:
            success = memory.upsert(task_id, content, title=f"Unicode Test {task_id}")
            assert success, f"Failed to upsert {task_id}"

            result = memory.get(task_id)
            assert result is not None, f"Failed to retrieve {task_id}"
            assert result["content"] == content, f"Content corruption for {task_id}"

            # Test search with Unicode
            if "世界" in content:
                results = memory.search("世界", k=5)
                task_ids = [r.task_id for r in results]
                assert task_id in task_ids, f"Unicode search failed for {task_id}"

    def test_rapid_successive_operations(self, chaos_db):
        """Test system under rapid successive operations."""
        memory = Memory(db_path=chaos_db)

        # Rapid fire operations
        start_time = time.time()
        operations_completed = 0

        for i in range(200):
            task_id = f"rapid-{i:03d}"

            # Upsert
            success = memory.upsert(task_id, f"Rapid content {i}", title=f"Rapid {i}")
            if success:
                operations_completed += 1

            # Immediate get
            result = memory.get(task_id)
            if result is not None:
                operations_completed += 1

            # Every 10th operation, do a search
            if i % 10 == 0:
                results = memory.search(f"rapid content {i % 50}", k=3)
                operations_completed += 1

        total_time = time.time() - start_time
        ops_per_second = operations_completed / total_time

        # Should maintain reasonable throughput
        assert (
            ops_per_second > 50
        ), f"Throughput {ops_per_second:.1f} ops/sec too low for rapid operations"

        # Should complete most operations
        expected_ops = 200 * 2 + 20  # 200 upserts, 200 gets, 20 searches
        completion_rate = operations_completed / expected_ops
        assert completion_rate > 0.9, f"Completion rate {completion_rate:.2%} too low"

        print(
            f"Rapid operations: {operations_completed} ops in {total_time:.2f}s ({ops_per_second:.1f} ops/sec)"
        )
