import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.tasks.backups import create_backup_task, purge_old_backups_task


def test_backup_and_retention_flow(monkeypatch):
    """Running the backup task should create a new dump and purge old ones."""

    # Use a temp directory for BACKUP_DIR
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(settings, "BACKUP_DIR", tmpdir)
        backup_dir = Path(tmpdir)

        # Create an expired dump (older than retention)
        expired = backup_dir / "expired_dump.sql.gz"
        expired.touch()
        old_mtime = datetime.utcnow() - timedelta(
            days=settings.BACKUP_RETENTION_DAYS + 2
        )
        os.utime(expired, (old_mtime.timestamp(), old_mtime.timestamp()))

        # Create a fresh dump that should NOT be deleted
        fresh = backup_dir / "fresh_dump.sql.gz"
        fresh.touch()

        # Monkeypatch `create_dump` to avoid calling pg_dump
        def _fake_create_dump(output_dir: Path, label: str | None = None):
            path = output_dir / f"{label or 'test'}.sql.gz"
            path.touch()
            return path

        monkeypatch.setattr("app.tasks.backups.create_dump", _fake_create_dump)

        # Mock the async task call to avoid Redis dependency
        with patch("app.tasks.backups.purge_old_backups_task.delay") as mock_delay:
            # Run backup task synchronously
            new_dump_path = Path(create_backup_task())
            assert new_dump_path.exists()

            # Verify the async task was called
            mock_delay.assert_called_once()

        # Run retention purge explicitly (in eager Celery this would run automatically)
        purged_count = purge_old_backups_task()
        assert purged_count == 1
        assert not expired.exists()
        assert fresh.exists()
        assert new_dump_path.exists()
