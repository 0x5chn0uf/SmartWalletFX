"""
Integration tests for the Memory Bridge system.
Tests the complete workflow from file indexing to search retrieval.
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from serena.infrastructure.database import init_database
from serena.infrastructure.indexer import MemoryIndexer as IndexManager
from serena.services.memory_impl import Memory


class TestMemoryIntegration:
    """Integration tests for the complete memory bridge workflow."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with test markdown files."""
        workspace = tempfile.mkdtemp()

        # Create test directory structure
        archive_dir = Path(workspace) / ".taskmaster" / "memory-bank" / "archive"
        reflection_dir = Path(workspace) / ".taskmaster" / "memory-bank" / "reflection"
        serena_dir = Path(workspace) / ".serena" / "memories"

        for dir_path in [archive_dir, reflection_dir, serena_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create test markdown files
        test_files = {
            archive_dir
            / "task-1.md": """---
task: 1
title: "Authentication System"
completed: 2025-01-01T10:00:00Z
status: done
---

# Authentication System

Implemented JWT-based authentication with the following features:
- User registration and login
- JWT token generation and validation
- Password hashing with bcrypt
- Token refresh mechanism

## Implementation Details

The authentication system uses FastAPI for the endpoints and SQLAlchemy for database operations.
""",
            archive_dir
            / "task-2.md": """---
task: 2
title: "Database Migration"
completed: 2025-01-02T14:30:00Z
status: done
---

# Database Migration

Updated the database schema to support new user roles and permissions.

## Changes Made

- Added roles table
- Added user_roles junction table
- Updated user table with additional fields
- Created migration scripts for existing data
""",
            reflection_dir
            / "reflection-1.md": """---
task: 1
title: "Authentication System Reflection"
created: 2025-01-01T16:00:00Z
---

# Reflection: Authentication System

## What Went Well

- JWT implementation was straightforward using PyJWT
- Password hashing with bcrypt worked as expected
- FastAPI dependency injection made testing easier

## Challenges

- Token refresh logic required careful consideration of security
- Database connection handling needed optimization

## Lessons Learned

- Always validate tokens on every protected endpoint
- Use environment variables for JWT secrets
- Implement proper error handling for expired tokens
""",
            serena_dir
            / "user-management.md": """# User Management Patterns

This document captures common patterns for user management in the application.

## Registration Flow

1. Validate user input
2. Check for existing email
3. Hash password with bcrypt
4. Store user in database
5. Send welcome email

## Authentication Flow

1. Validate credentials
2. Generate JWT token
3. Return token with user info
4. Store session information
""",
        }

        for file_path, content in test_files.items():
            file_path.write_text(content)

        yield workspace

        # Cleanup
        shutil.rmtree(workspace)

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        init_database(db_path)
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

    def test_complete_indexing_workflow(self, temp_workspace, temp_db):
        """Test the complete workflow from file scanning to database indexing."""
        # Change to the workspace directory for indexing
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)

        try:
            # Initialize the indexer
            indexer = IndexManager(db_path=temp_db)

            # Run the indexing process
            result = indexer.index_files(
                directories=[
                    ".taskmaster/memory-bank/archive",
                    ".taskmaster/memory-bank/reflection",
                    ".serena/memories",
                ]
            )

            # Verify indexing results
            assert result["files_found"] == 4
            assert result["files_indexed"] == 4
            assert result["files_skipped"] == 0
            assert result["files_failed"] == 0

            # Verify database contains the indexed content
            memory = Memory(db_path=temp_db)

            # Test retrieval of specific tasks
            task1 = memory.get("1")
            assert task1 is not None
            assert task1["title"] == "Authentication System"
            assert "JWT-based authentication" in task1["content"]

            task2 = memory.get("2")
            assert task2 is not None
            assert task2["title"] == "Database Migration"
            assert "roles table" in task2["content"]

            # Test search functionality
            auth_results = memory.search("JWT authentication", k=5)
            assert len(auth_results) > 0

            # Verify task 1 appears in authentication search
            task_ids = [r.task_id for r in auth_results]
            assert "1" in task_ids

            # Test database-related search
            db_results = memory.search("database schema migration", k=5)
            assert len(db_results) > 0

            # Verify task 2 appears in database search
            db_task_ids = [r.task_id for r in db_results]
            assert "2" in db_task_ids

        finally:
            os.chdir(original_cwd)

    def test_incremental_indexing(self, temp_workspace, temp_db):
        """Test that incremental indexing works correctly."""
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)

        try:
            indexer = IndexManager(db_path=temp_db)
            memory = Memory(db_path=temp_db)

            # First indexing run
            result1 = indexer.index_files(
                directories=[".taskmaster/memory-bank/archive"]
            )
            assert result1["files_indexed"] == 2  # Only archive files

            # Add a new file
            new_file = (
                Path(temp_workspace)
                / ".taskmaster"
                / "memory-bank"
                / "archive"
                / "task-3.md"
            )
            new_file.write_text(
                """---
task: 3
title: "API Endpoints"
completed: 2025-01-03T09:00:00Z
status: done
---

# API Endpoints

Created REST API endpoints for user management and authentication.
"""
            )

            # Second indexing run should pick up the new file
            result2 = indexer.index_files(
                directories=[".taskmaster/memory-bank/archive"]
            )
            assert result2["files_found"] == 3
            assert result2["files_indexed"] == 1  # Only the new file
            assert result2["files_skipped"] == 2  # Previous files skipped

            # Verify the new task is retrievable
            task3 = memory.get("3")
            assert task3 is not None
            assert task3["title"] == "API Endpoints"

        finally:
            os.chdir(original_cwd)

    def test_deduplication_across_indexing_runs(self, temp_workspace, temp_db):
        """Test that deduplication works across multiple indexing runs."""
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)

        try:
            indexer = IndexManager(db_path=temp_db)
            memory = Memory(db_path=temp_db)

            # First indexing run
            result1 = indexer.index_files(
                directories=[".taskmaster/memory-bank/archive"]
            )
            assert result1["files_indexed"] == 2

            # Modify timestamp but keep content the same (should be deduplicated)
            task_file = (
                Path(temp_workspace)
                / ".taskmaster"
                / "memory-bank"
                / "archive"
                / "task-1.md"
            )
            original_content = task_file.read_text()

            # Touch the file to change mtime
            import time

            time.sleep(0.1)
            task_file.write_text(original_content)

            # Second indexing run should skip the unchanged file
            result2 = indexer.index_files(
                directories=[".taskmaster/memory-bank/archive"]
            )
            assert result2["files_skipped"] == 2  # Both files should be skipped
            assert result2["files_indexed"] == 0

            # Health check should still show the same counts
            health = memory.health()
            assert health.archive_count == 2

        finally:
            os.chdir(original_cwd)

    def test_search_ranking_and_relevance(self, temp_workspace, temp_db):
        """Test that search results are properly ranked by relevance."""
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)

        try:
            # Index all files
            indexer = IndexManager(db_path=temp_db)
            indexer.index_files(
                directories=[
                    ".taskmaster/memory-bank/archive",
                    ".taskmaster/memory-bank/reflection",
                    ".serena/memories",
                ]
            )

            memory = Memory(db_path=temp_db)

            # Search for "authentication" - should rank auth-related content higher
            results = memory.search("authentication JWT", k=10)

            # Should have results
            assert len(results) > 0

            # Results should be ordered by relevance score (descending)
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)

            # The authentication task should rank higher than others
            top_result = results[0]
            assert top_result.score > 0.3  # Should have decent similarity

            # Test that more specific queries return more relevant results
            specific_results = memory.search("JWT token authentication FastAPI", k=5)
            general_results = memory.search("system", k=5)

            # Specific query should have higher top score
            if specific_results and general_results:
                assert specific_results[0].score >= general_results[0].score

        finally:
            os.chdir(original_cwd)

    def test_migration_script_integration(self, temp_workspace, temp_db):
        """Test the migration script functionality."""
        from scripts.migrate import migrate_files

        original_cwd = os.getcwd()
        os.chdir(temp_workspace)

        try:
            # Run migration script
            result = migrate_files(
                db_path=temp_db,
                directories=[
                    ".taskmaster/memory-bank/archive",
                    ".taskmaster/memory-bank/reflection",
                    ".serena/memories",
                ],
                dry_run=False,
                force=True,
            )

            # Verify migration results
            assert result["files_found"] == 4
            assert result["files_indexed"] == 4
            assert result["files_failed"] == 0

            # Verify searchable content
            memory = Memory(db_path=temp_db)
            results = memory.search("authentication", k=10)
            assert len(results) > 0

            # Verify health metrics
            health = memory.health()
            assert health.archive_count == 4
            assert health.embedding_count > 0
            assert health.database_size > 0

        finally:
            os.chdir(original_cwd)


@pytest.mark.slow
class TestMemoryBridgeMigration:
    """Tests for the migration functionality specifically."""

    def test_migration_with_existing_data(self, temp_db):
        """Test migration handles existing data correctly."""
        memory = Memory(db_path=temp_db)

        # Manually insert some data
        memory.upsert("existing-1", "# Existing Task\n\nThis task already exists.")

        # Verify it exists
        existing = memory.get("existing-1")
        assert existing is not None

        # Create a temp file with same task ID but different content
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_dir = Path(temp_dir) / ".taskmaster" / "memory-bank" / "archive"
            archive_dir.mkdir(parents=True)

            task_file = archive_dir / "existing-1.md"
            task_file.write_text(
                """---
task: existing-1
title: "Updated Task"
completed: 2025-01-01T10:00:00Z
---

# Updated Task

This is updated content for the existing task.
"""
            )

            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                indexer = IndexManager(db_path=temp_db)
                result = indexer.index_files(
                    directories=[".taskmaster/memory-bank/archive"]
                )

                # Should update the existing task
                assert result["files_indexed"] == 1

                # Verify content is updated
                updated = memory.get("existing-1")
                assert updated is not None
                assert "Updated Task" in updated["content"]
                assert "updated content" in updated["content"]

            finally:
                os.chdir(original_cwd)
