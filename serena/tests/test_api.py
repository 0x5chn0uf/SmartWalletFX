"""
Tests for the Memory API.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from serena.infrastructure.database import init_database
from serena.core.models import TaskKind, TaskStatus
from serena.services.memory_impl import Memory


class TestMemoryAPI:
    """Test suite for the Memory API."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        # Initialize database
        init_database(db_path)

        yield db_path

        # Cleanup
        try:
            os.unlink(db_path)
            # Also clean up WAL and SHM files if they exist
            for suffix in ["-wal", "-shm"]:
                wal_path = db_path + suffix
                if os.path.exists(wal_path):
                    os.unlink(wal_path)
        except OSError:
            pass

    @pytest.fixture
    def memory(self, temp_db):
        """Create a Memory instance with temporary database."""
        return Memory(db_path=temp_db)

    def test_memory_initialization(self, temp_db):
        """Test Memory instance initialization."""
        memory = Memory(db_path=temp_db)
        assert memory.db_path == temp_db
        assert memory.cache_size == 512

    def test_upsert_and_get(self, memory):
        """Test basic upsert and get operations."""
        task_id = "test-123"
        title = "Test Task"
        content = """# Test Task
        
        This is a test task for the memory bridge.
        
        ## Details
        
        Some implementation details here.
        """

        # Upsert the task
        success = memory.upsert(
            task_id=task_id,
            markdown_text=content,
            title=title,
            kind=TaskKind.ARCHIVE,
            status=TaskStatus.DONE,
            completed_at=datetime.now(),
        )

        assert success is True

        # Retrieve the task
        result = memory.get(task_id)
        assert result is not None
        assert result["task_id"] == task_id
        assert result["title"] == title
        assert result["kind"] == TaskKind.ARCHIVE.value
        assert result["status"] == TaskStatus.DONE.value
        assert result["content"] == content

    def test_get_nonexistent_task(self, memory):
        """Test getting a task that doesn't exist."""
        result = memory.get("nonexistent-task")
        assert result is None

    def test_deduplication(self, memory):
        """Test content deduplication based on SHA-256."""
        content = "# Same Content\n\nThis content is identical."

        # Insert first task
        success1 = memory.upsert("task-1", content)
        assert success1 is True

        # Try to insert second task with same content
        success2 = memory.upsert("task-2", content)
        assert success2 is False  # Should be rejected due to duplication

        # Verify only first task exists
        task1 = memory.get("task-1")
        task2 = memory.get("task-2")

        assert task1 is not None
        assert task2 is None

    def test_search_functionality(self, memory):
        """Test semantic search functionality."""
        # Add some test content
        test_tasks = [
            (
                "auth-1",
                "Authentication System",
                "JWT token authentication with refresh tokens",
            ),
            (
                "auth-2",
                "OAuth Integration",
                "OAuth2 flow with Google and GitHub providers",
            ),
            (
                "db-1",
                "Database Schema",
                "PostgreSQL schema with user tables and indexes",
            ),
            (
                "api-1",
                "REST API Design",
                "FastAPI endpoints with proper error handling",
            ),
        ]

        for task_id, title, content in test_tasks:
            memory.upsert(task_id, f"# {title}\n\n{content}")

        # Search for authentication-related content
        results = memory.search("authentication oauth", k=3)

        assert len(results) > 0

        # Results should be ranked by relevance
        for result in results:
            assert result.score > 0
            assert result.task_id in ["auth-1", "auth-2", "db-1", "api-1"]
            assert result.title in [title for _, title, _ in test_tasks]

    def test_latest_functionality(self, memory):
        """Test getting latest tasks."""
        # Add tasks with different completion dates
        base_time = datetime.now()

        for i in range(5):
            completion_time = base_time.replace(hour=i)
            memory.upsert(
                task_id=f"task-{i}",
                markdown_text=f"# Task {i}\n\nContent for task {i}",
                completed_at=completion_time,
            )

        # Get latest 3 tasks
        results = memory.latest(n=3)

        assert len(results) == 3

        # Should be ordered by completion time (most recent first)
        completion_times = [r.completed_at for r in results if r.completed_at]
        assert completion_times == sorted(completion_times, reverse=True)

    def test_health_info(self, memory):
        """Test health information reporting."""
        # Add some test data
        memory.upsert("health-test", "# Health Test\n\nTest content")

        health = memory.health()

        assert health.archive_count >= 1
        assert health.embedding_count >= 1
        assert health.database_size > 0
        assert isinstance(health.embedding_versions, dict)

    def test_cache_functionality(self, memory):
        """Test LRU cache functionality."""
        task_id = "cache-test"
        content = "# Cache Test\n\nTest caching behavior"

        # Insert task
        memory.upsert(task_id, content)

        # First get - should cache the result
        result1 = memory.get(task_id)
        assert result1 is not None

        # Second get - should use cache
        result2 = memory.get(task_id)
        assert result2 is not None
        assert result1 == result2

        # Cache should be cleared after upsert
        memory.upsert(task_id, content + "\n\nUpdated content")
        result3 = memory.get(task_id)
        assert result3 is not None
        assert result3["content"] != result1["content"]


@pytest.mark.integration
class TestMemoryIntegration:
    """Integration tests requiring external dependencies."""

    def test_embedding_generation(self, memory):
        """Test that embeddings are actually generated."""
        content = """# Machine Learning Task
        
        Implement a neural network for image classification using PyTorch.
        The model should use convolutional layers and achieve 95% accuracy.
        """

        success = memory.upsert("ml-task", content)
        assert success is True

        # Verify embeddings were created
        health = memory.health()
        assert health.embedding_count > 0

        # Test semantic search works
        results = memory.search("neural network pytorch", k=1)
        assert len(results) == 1
        assert results[0].task_id == "ml-task"
        assert results[0].score > 0.3  # Should have decent similarity
