"""
Performance tests for the Memory Bridge system.
Tests latency requirements and scalability benchmarks.
"""

import concurrent.futures
import os
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest

from serena.core.models import TaskKind, TaskStatus
from serena.indexer import IndexManager
from serena.infrastructure.database import init_database
from serena.services.memory_impl import Memory


class TestMemoryPerformance:
    """Performance tests for the memory bridge system."""

    @pytest.fixture
    def large_dataset_db(self):
        """Create a database with a large dataset for performance testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        init_database(db_path)
        memory = Memory(db_path=db_path)

        # Generate test data simulating 1000 tasks
        for i in range(1000):
            task_id = f"perf-task-{i:04d}"
            content = f"""# Performance Test Task {i}

This is a performance test task with ID {i}.

## Description

This task simulates a real archive entry with sufficient content to test
embedding generation and search performance. It contains multiple paragraphs
and technical details to ensure realistic content size.

## Technical Details

- Task ID: {task_id}
- Category: {"backend" if i % 3 == 0 else "frontend" if i % 3 == 1 else "infrastructure"}
- Priority: {"high" if i % 5 == 0 else "medium" if i % 5 in [1, 2] else "low"}
- Technology: {"Python" if i % 4 == 0 else "JavaScript" if i % 4 == 1 else "Docker" if i % 4 == 2 else "SQL"}

## Implementation Notes

The implementation involved several key components:
1. Database schema design
2. API endpoint creation
3. Authentication middleware
4. Error handling
5. Unit test coverage

## Lessons Learned

- Performance optimization is crucial for large datasets
- Proper indexing significantly improves query performance
- Caching strategies should be implemented for frequently accessed data
- Error handling should be comprehensive and user-friendly

## Future Improvements

- Add more comprehensive logging
- Implement advanced caching mechanisms
- Consider database sharding for larger datasets
- Enhance search capabilities with full-text search
"""

            success = memory.upsert(
                task_id=task_id,
                markdown_text=content,
                title=f"Performance Test Task {i}",
                kind=TaskKind.ARCHIVE if i % 2 == 0 else TaskKind.REFLECTION,
                status=TaskStatus.DONE,
                completed_at=datetime.now(),
            )
            assert success, f"Failed to insert task {task_id}"

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

    @pytest.mark.benchmark
    def test_get_latency_cold_cache(self, large_dataset_db):
        """Test get() latency on cold cache meets <50ms requirement."""
        memory = Memory(db_path=large_dataset_db, cache_size=0)  # Disable cache

        # Test multiple random tasks
        test_tasks = ["perf-task-0001", "perf-task-0500", "perf-task-0999"]
        latencies = []

        for task_id in test_tasks:
            start_time = time.perf_counter()
            result = memory.get(task_id)
            end_time = time.perf_counter()

            assert result is not None, f"Task {task_id} not found"
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

            # Individual get should be under 50ms
            assert (
                latency_ms < 50
            ), f"Get latency {latency_ms:.2f}ms exceeds 50ms target for {task_id}"

        # Average latency should also be well under target
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 30, f"Average get latency {avg_latency:.2f}ms too high"

        print(f"Get latencies: {[f'{l:.2f}ms' for l in latencies]}")
        print(f"Average get latency: {avg_latency:.2f}ms")

    @pytest.mark.benchmark
    def test_get_latency_hot_cache(self, large_dataset_db):
        """Test get() latency with hot cache is significantly faster."""
        memory = Memory(db_path=large_dataset_db, cache_size=512)

        task_id = "perf-task-0100"

        # Warm up the cache
        memory.get(task_id)

        # Test cached access
        latencies = []
        for _ in range(10):
            start_time = time.perf_counter()
            result = memory.get(task_id)
            end_time = time.perf_counter()

            assert result is not None
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

        avg_latency = sum(latencies) / len(latencies)

        # Cached access should be under 5ms
        assert avg_latency < 5, f"Cached get latency {avg_latency:.2f}ms too high"

        print(f"Cached get average latency: {avg_latency:.2f}ms")

    @pytest.mark.benchmark
    def test_search_latency(self, large_dataset_db):
        """Test search() latency meets <100ms requirement for 1000 archives."""
        memory = Memory(db_path=large_dataset_db)

        # Test various search queries
        search_queries = [
            "Python backend implementation",
            "JavaScript frontend component",
            "Docker infrastructure setup",
            "SQL database optimization",
            "authentication middleware security",
            "performance optimization caching",
            "error handling logging",
        ]

        latencies = []

        for query in search_queries:
            start_time = time.perf_counter()
            results = memory.search(query, k=10)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

            # Should return relevant results
            assert len(results) > 0, f"No results for query: {query}"

            # Individual search should be under 100ms
            assert (
                latency_ms < 100
            ), f"Search latency {latency_ms:.2f}ms exceeds 100ms target for '{query}'"

        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 75, f"Average search latency {avg_latency:.2f}ms too high"

        print(f"Search latencies: {[f'{l:.2f}ms' for l in latencies]}")
        print(f"Average search latency: {avg_latency:.2f}ms")

    @pytest.mark.benchmark
    def test_search_result_quality(self, large_dataset_db):
        """Test that search results are relevant and properly ranked."""
        memory = Memory(db_path=large_dataset_db)

        # Test specific technology searches
        queries_and_expectations = [
            ("Python backend", "Python"),
            ("JavaScript frontend", "JavaScript"),
            ("Docker infrastructure", "Docker"),
            ("SQL database", "SQL"),
        ]

        for query, expected_tech in queries_and_expectations:
            results = memory.search(query, k=20)

            # Should have results
            assert len(results) > 0, f"No results for '{query}'"

            # Top results should be relevant (contain expected technology)
            top_5_contents = []
            for result in results[:5]:
                task = memory.get(result.task_id)
                if task:
                    top_5_contents.append(task["content"])

            # At least 60% of top 5 should contain the expected technology
            relevant_count = sum(
                1 for content in top_5_contents if expected_tech in content
            )
            relevance_ratio = (
                relevant_count / len(top_5_contents) if top_5_contents else 0
            )

            assert (
                relevance_ratio >= 0.6
            ), f"Only {relevance_ratio:.1%} of top results relevant for '{query}'"

            # Scores should be in descending order
            scores = [r.score for r in results]
            assert scores == sorted(
                scores, reverse=True
            ), f"Results not properly ranked for '{query}'"

    @pytest.mark.benchmark
    def test_concurrent_read_performance(self, large_dataset_db):
        """Test concurrent read performance with multiple threads."""
        memory = Memory(db_path=large_dataset_db)

        def read_worker(worker_id, num_operations=50):
            """Worker function for concurrent reads."""
            latencies = []
            for i in range(num_operations):
                task_id = f"perf-task-{(worker_id * num_operations + i) % 1000:04d}"

                start_time = time.perf_counter()
                result = memory.get(task_id)
                end_time = time.perf_counter()

                assert result is not None, f"Task {task_id} not found"
                latencies.append((end_time - start_time) * 1000)

            return latencies

        # Test with 4 concurrent readers
        num_workers = 4
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            start_time = time.perf_counter()

            # Submit worker tasks
            futures = [executor.submit(read_worker, i) for i in range(num_workers)]

            # Collect results
            all_latencies = []
            for future in concurrent.futures.as_completed(futures):
                worker_latencies = future.result()
                all_latencies.extend(worker_latencies)

            end_time = time.perf_counter()

        # Analyze results
        total_operations = len(all_latencies)
        total_time = end_time - start_time
        throughput = total_operations / total_time

        avg_latency = sum(all_latencies) / len(all_latencies)
        max_latency = max(all_latencies)

        # Performance targets
        assert (
            avg_latency < 75
        ), f"Average concurrent read latency {avg_latency:.2f}ms too high"
        assert (
            max_latency < 200
        ), f"Max concurrent read latency {max_latency:.2f}ms too high"
        assert (
            throughput > 50
        ), f"Concurrent read throughput {throughput:.1f} ops/sec too low"

        print(f"Concurrent reads: {total_operations} operations in {total_time:.2f}s")
        print(f"Throughput: {throughput:.1f} operations/second")
        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"Max latency: {max_latency:.2f}ms")

    @pytest.mark.benchmark
    def test_upsert_performance(self, large_dataset_db):
        """Test upsert performance for new content."""
        memory = Memory(db_path=large_dataset_db)

        # Test inserting new tasks
        new_tasks = []
        for i in range(10):
            task_id = f"new-task-{i:04d}"
            content = f"# New Task {i}\n\nThis is a new task for performance testing."
            new_tasks.append((task_id, content))

        upsert_latencies = []

        for task_id, content in new_tasks:
            start_time = time.perf_counter()
            success = memory.upsert(task_id, content, title=f"New Task {task_id}")
            end_time = time.perf_counter()

            assert success, f"Failed to upsert {task_id}"

            latency_ms = (end_time - start_time) * 1000
            upsert_latencies.append(latency_ms)

        avg_upsert_latency = sum(upsert_latencies) / len(upsert_latencies)
        max_upsert_latency = max(upsert_latencies)

        # Upsert should complete in reasonable time (including embedding generation)
        assert (
            avg_upsert_latency < 500
        ), f"Average upsert latency {avg_upsert_latency:.2f}ms too high"
        assert (
            max_upsert_latency < 1000
        ), f"Max upsert latency {max_upsert_latency:.2f}ms too high"

        print(f"Upsert latencies: {[f'{l:.2f}ms' for l in upsert_latencies]}")
        print(f"Average upsert latency: {avg_upsert_latency:.2f}ms")

    @pytest.mark.benchmark
    def test_database_size_efficiency(self, large_dataset_db):
        """Test that database size remains reasonable for large datasets."""
        memory = Memory(db_path=large_dataset_db)
        health = memory.health()

        # Database should be reasonably sized
        db_size_mb = health.database_size / (1024 * 1024)

        # For 1000 tasks, database should be under 50MB
        assert (
            db_size_mb < 50
        ), f"Database size {db_size_mb:.2f}MB too large for 1000 tasks"

        # Should have expected number of records
        assert (
            health.archive_count == 1000
        ), f"Expected 1000 archives, got {health.archive_count}"
        assert (
            health.embedding_count >= 1000
        ), f"Expected at least 1000 embeddings, got {health.embedding_count}"

        print(f"Database size: {db_size_mb:.2f}MB for {health.archive_count} archives")
        print(f"Embeddings: {health.embedding_count}")
        print(
            f"Average size per archive: {(db_size_mb * 1024) / health.archive_count:.2f}KB"
        )

    @pytest.mark.benchmark
    def test_cache_hit_rate(self, large_dataset_db):
        """Test LRU cache effectiveness."""
        cache_size = 100
        memory = Memory(db_path=large_dataset_db, cache_size=cache_size)

        # Access a subset of tasks multiple times
        test_task_ids = [f"perf-task-{i:04d}" for i in range(0, 50, 5)]  # 10 tasks

        # First pass - populate cache
        for task_id in test_task_ids:
            result = memory.get(task_id)
            assert result is not None

        # Second pass - should be mostly cached
        cached_latencies = []
        for task_id in test_task_ids:
            start_time = time.perf_counter()
            result = memory.get(task_id)
            end_time = time.perf_counter()

            assert result is not None
            latency_ms = (end_time - start_time) * 1000
            cached_latencies.append(latency_ms)

        avg_cached_latency = sum(cached_latencies) / len(cached_latencies)

        # Cached access should be very fast
        assert (
            avg_cached_latency < 2
        ), f"Cached access latency {avg_cached_latency:.2f}ms too high"

        print(f"Cache hit latency: {avg_cached_latency:.2f}ms average")


@pytest.mark.slow
class TestMemoryStressTest:
    """Stress tests for the memory bridge system."""

    def test_memory_usage_under_load(self, large_dataset_db):
        """Test memory usage remains stable under heavy load."""
        import gc

        import psutil

        memory = Memory(db_path=large_dataset_db)
        process = psutil.Process()

        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many operations
        for i in range(100):
            # Random searches
            results = memory.search(f"test query {i % 10}", k=5)

            # Random gets
            task_id = f"perf-task-{i % 1000:04d}"
            result = memory.get(task_id)
            assert result is not None

            # Force garbage collection periodically
            if i % 25 == 0:
                gc.collect()

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        # Memory growth should be minimal (under 100MB)
        assert (
            memory_growth < 100
        ), f"Memory grew by {memory_growth:.2f}MB during stress test"

        print(
            f"Memory usage: {initial_memory:.2f}MB -> {final_memory:.2f}MB (growth: {memory_growth:.2f}MB)"
        )

    def test_rapid_concurrent_access(self, large_dataset_db):
        """Test system stability under rapid concurrent access."""
        memory = Memory(db_path=large_dataset_db)

        def rapid_worker(worker_id, duration_seconds=5):
            """Worker that performs rapid operations for specified duration."""
            start_time = time.time()
            operations = 0
            errors = 0

            while time.time() - start_time < duration_seconds:
                try:
                    # Alternate between searches and gets
                    if operations % 2 == 0:
                        task_id = f"perf-task-{(worker_id + operations) % 1000:04d}"
                        result = memory.get(task_id)
                        assert result is not None
                    else:
                        query = f"test query {operations % 10}"
                        results = memory.search(query, k=3)
                        assert len(results) >= 0  # May be empty for some queries

                    operations += 1

                except Exception as e:
                    errors += 1
                    if errors > 10:  # Too many errors
                        raise e

            return operations, errors

        # Test with 8 concurrent workers for 5 seconds
        num_workers = 8
        duration = 5

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(rapid_worker, i, duration) for i in range(num_workers)
            ]

            results = []
            for future in concurrent.futures.as_completed(futures):
                operations, errors = future.result()
                results.append((operations, errors))

        # Analyze results
        total_operations = sum(ops for ops, errors in results)
        total_errors = sum(errors for ops, errors in results)

        # Should handle high load without errors
        error_rate = total_errors / total_operations if total_operations > 0 else 0
        assert error_rate < 0.01, f"Error rate {error_rate:.2%} too high under stress"

        # Should achieve reasonable throughput
        throughput = total_operations / duration
        assert (
            throughput > 200
        ), f"Throughput {throughput:.1f} ops/sec too low under stress"

        print(f"Stress test: {total_operations} operations in {duration}s")
        print(f"Throughput: {throughput:.1f} operations/second")
        print(f"Error rate: {error_rate:.3%}")
