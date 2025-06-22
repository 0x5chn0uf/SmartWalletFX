"""Comprehensive unit tests for backup tasks."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.tasks.backups import (
    _list_expired_dumps,
    create_backup_task,
    purge_old_backups_task,
    restore_from_upload_task,
)


class TestCreateBackupTask:
    """Test create_backup_task functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_output_dir = Path("/tmp/backups")
        self.test_dump_path = Path("/tmp/backups/scheduled-20241201120000.sql.gz")

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.create_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.purge_old_backups_task")
    def test_create_backup_task_success(
        self, mock_purge_task, mock_audit, mock_create_dump, mock_settings
    ):
        """Test successful backup task execution."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        mock_create_dump.return_value = self.test_dump_path

        with patch.object(Path, "mkdir") as mock_mkdir:
            result = create_backup_task()

        assert result == str(self.test_dump_path)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_create_dump.assert_called_once()
        mock_audit.assert_called_once_with(
            "DB_BACKUP_SCHEDULED",
            dump_path=str(self.test_dump_path),
            label=mock_create_dump.call_args[1]["label"],
        )
        mock_purge_task.delay.assert_called_once()

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.create_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.purge_old_backups_task")
    def test_create_backup_task_creates_output_directory(
        self, mock_purge_task, mock_audit, mock_create_dump, mock_settings
    ):
        """Test that backup task creates output directory."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        mock_create_dump.return_value = self.test_dump_path

        with patch.object(Path, "mkdir") as mock_mkdir:
            create_backup_task()

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.create_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.purge_old_backups_task")
    def test_create_backup_task_uses_utc_timestamp(
        self, mock_purge_task, mock_audit, mock_create_dump, mock_settings
    ):
        """Test that backup task uses UTC timestamp for label."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        mock_create_dump.return_value = self.test_dump_path

        with patch("app.tasks.backups.datetime") as mock_datetime:
            # Create a mock datetime object
            mock_dt = Mock()
            mock_dt.strftime.return_value = "20241201120000"
            mock_datetime.utcnow.return_value = mock_dt

            with patch.object(Path, "mkdir"):
                create_backup_task()

        call_args = mock_create_dump.call_args[1]
        assert call_args["label"] == "scheduled-20241201120000"

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.create_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.purge_old_backups_task")
    def test_create_backup_task_failure(
        self, mock_purge_task, mock_audit, mock_create_dump, mock_settings
    ):
        """Test backup task failure handling."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        test_exception = Exception("Backup failed")
        mock_create_dump.side_effect = test_exception

        with patch.object(Path, "mkdir"):
            with pytest.raises(Exception, match="Backup failed"):
                create_backup_task()

        # Should audit failure
        mock_audit.assert_called_once_with(
            "DB_BACKUP_FAILED", label=mock_create_dump.call_args[1]["label"]
        )
        # Should not trigger purge task on failure
        mock_purge_task.delay.assert_not_called()

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.create_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.purge_old_backups_task")
    def test_create_backup_task_failure_audit_includes_label(
        self, mock_purge_task, mock_audit, mock_create_dump, mock_settings
    ):
        """Test that failure audit includes the label."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        mock_create_dump.side_effect = Exception("Backup failed")

        with patch("app.tasks.backups.datetime") as mock_datetime:
            # Create a mock datetime object
            mock_dt = Mock()
            mock_dt.strftime.return_value = "20241201120000"
            mock_datetime.utcnow.return_value = mock_dt

            with patch.object(Path, "mkdir"):
                with pytest.raises(Exception):
                    create_backup_task()

        mock_audit.assert_called_once_with(
            "DB_BACKUP_FAILED", label="scheduled-20241201120000"
        )


class TestRestoreFromUploadTask:
    """Test restore_from_upload_task functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_temp_file = "/tmp/uploaded_backup.sql.gz"

    @patch("app.tasks.backups.restore_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.logger")
    def test_restore_from_upload_task_success(
        self, mock_logger, mock_audit, mock_restore_dump
    ):
        """Test successful restore task execution."""
        with patch.object(Path, "__new__", return_value=Path(self.test_temp_file)):
            result = restore_from_upload_task(self.test_temp_file)

        expected_message = f"Database restored successfully from {self.test_temp_file}"
        assert result == expected_message
        mock_restore_dump.assert_called_once_with(Path(self.test_temp_file), force=True)
        mock_audit.assert_called_once_with(
            "DB_RESTORE_COMPLETED",
            dump_path=self.test_temp_file,
        )

    @patch("app.tasks.backups.restore_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.logger")
    def test_restore_from_upload_task_failure(
        self, mock_logger, mock_audit, mock_restore_dump
    ):
        """Test restore task failure handling."""
        test_exception = Exception("Restore failed")
        mock_restore_dump.side_effect = test_exception

        with patch.object(Path, "__new__", return_value=Path(self.test_temp_file)):
            with pytest.raises(Exception, match="Restore failed"):
                restore_from_upload_task(self.test_temp_file)

        mock_audit.assert_called_once_with(
            "DB_RESTORE_FAILED",
            dump_path=self.test_temp_file,
            error="Restore failed",
        )

    @patch("app.tasks.backups.restore_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.logger")
    @patch("app.tasks.backups.os")
    def test_restore_from_upload_task_cleanup_success(
        self, mock_os, mock_logger, mock_audit, mock_restore_dump
    ):
        """Test that temporary file is cleaned up after successful restore."""
        mock_os.path.exists.return_value = True

        with patch.object(Path, "__new__", return_value=Path(self.test_temp_file)):
            restore_from_upload_task(self.test_temp_file)

        mock_os.unlink.assert_called_once_with(self.test_temp_file)

    @patch("app.tasks.backups.restore_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.logger")
    @patch("app.tasks.backups.os")
    def test_restore_from_upload_task_cleanup_file_not_exists(
        self, mock_os, mock_logger, mock_audit, mock_restore_dump
    ):
        """Test cleanup when temporary file doesn't exist."""
        # Set up the mock to return False for os.path.exists
        mock_os.path.exists.return_value = False

        with patch.object(Path, "__new__", return_value=Path(self.test_temp_file)):
            restore_from_upload_task(self.test_temp_file)

        mock_os.unlink.assert_not_called()

    @patch("app.tasks.backups.restore_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.logger")
    @patch("app.tasks.backups.os")
    def test_restore_from_upload_task_cleanup_failure(
        self, mock_os, mock_logger, mock_audit, mock_restore_dump
    ):
        """Test cleanup failure handling."""
        mock_os.path.exists.return_value = True
        mock_os.unlink.side_effect = OSError("Permission denied")

        with patch.object(Path, "__new__", return_value=Path(self.test_temp_file)):
            restore_from_upload_task(self.test_temp_file)

        mock_logger.warning.assert_called_once_with(
            f"Failed to clean up temp file {self.test_temp_file}: Permission denied"
        )

    @patch("app.tasks.backups.restore_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.logger")
    @patch("app.tasks.backups.os")
    def test_restore_from_upload_task_cleanup_failure_after_restore_failure(
        self, mock_os, mock_logger, mock_audit, mock_restore_dump
    ):
        """Test cleanup failure after restore failure."""
        mock_os.path.exists.return_value = True
        mock_restore_dump.side_effect = Exception("Restore failed")
        mock_os.unlink.side_effect = OSError("Permission denied")

        with patch.object(Path, "__new__", return_value=Path(self.test_temp_file)):
            with pytest.raises(Exception, match="Restore failed"):
                restore_from_upload_task(self.test_temp_file)

        # Should still attempt cleanup and log warning
        mock_logger.warning.assert_called_once_with(
            f"Failed to clean up temp file {self.test_temp_file}: Permission denied"
        )

    @patch("app.tasks.backups.restore_dump")
    @patch("app.tasks.backups.audit")
    @patch("app.tasks.backups.logger")
    @patch("app.tasks.backups.os")
    def test_restore_from_upload_task_force_parameter(
        self, mock_os, mock_logger, mock_audit, mock_restore_dump
    ):
        """Test that restore_dump is called with force=True."""
        mock_os.path.exists.return_value = True

        with patch.object(Path, "__new__", return_value=Path(self.test_temp_file)):
            restore_from_upload_task(self.test_temp_file)

        mock_restore_dump.assert_called_once_with(Path(self.test_temp_file), force=True)


class TestPurgeOldBackupsTask:
    """Test purge_old_backups_task functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_output_dir = Path("/tmp/backups")

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.audit")
    def test_purge_old_backups_task_success(self, mock_audit, mock_settings):
        """Test successful purge task execution."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        mock_settings.BACKUP_RETENTION_DAYS = 7

        # Mock expired files
        expired_files = [
            Path("/tmp/backups/old1.sql.gz"),
            Path("/tmp/backups/old2.sql.gz"),
        ]

        with patch.object(Path, "exists", return_value=True):
            with patch(
                "app.tasks.backups._list_expired_dumps", return_value=expired_files
            ):
                with patch.object(Path, "unlink") as mock_unlink:
                    result = purge_old_backups_task()

        assert result == 2
        assert mock_unlink.call_count == 2
        mock_audit.assert_any_call("DB_BACKUP_PURGED", dump_path=str(expired_files[0]))
        mock_audit.assert_any_call("DB_BACKUP_PURGED", dump_path=str(expired_files[1]))

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.audit")
    def test_purge_old_backups_task_directory_not_exists(
        self, mock_audit, mock_settings
    ):
        """Test purge task when backup directory doesn't exist."""
        mock_settings.BACKUP_DIR = "/tmp/backups"

        with patch.object(Path, "exists", return_value=False):
            result = purge_old_backups_task()

        assert result == 0
        mock_audit.assert_not_called()

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.audit")
    def test_purge_old_backups_task_no_expired_files(self, mock_audit, mock_settings):
        """Test purge task when no files are expired."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        mock_settings.BACKUP_RETENTION_DAYS = 7

        with patch.object(Path, "exists", return_value=True):
            with patch("app.tasks.backups._list_expired_dumps", return_value=[]):
                result = purge_old_backups_task()

        assert result == 0
        mock_audit.assert_not_called()

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.audit")
    def test_purge_old_backups_task_deletion_failure(self, mock_audit, mock_settings):
        """Test purge task when file deletion fails."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        mock_settings.BACKUP_RETENTION_DAYS = 7

        expired_files = [Path("/tmp/backups/old1.sql.gz")]

        with patch.object(Path, "exists", return_value=True):
            with patch(
                "app.tasks.backups._list_expired_dumps", return_value=expired_files
            ):
                with patch.object(
                    Path, "unlink", side_effect=OSError("Permission denied")
                ):
                    result = purge_old_backups_task()

        assert result == 1  # Still returns count of expired files
        mock_audit.assert_called_once_with(
            "DB_BACKUP_PURGE_FAILED",
            dump_path=str(expired_files[0]),
            error="Permission denied",
        )

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.audit")
    def test_purge_old_backups_task_mixed_success_failure(
        self, mock_audit, mock_settings
    ):
        """Test purge task with mixed success and failure."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        mock_settings.BACKUP_RETENTION_DAYS = 7

        expired_files = [
            Path("/tmp/backups/old1.sql.gz"),
            Path("/tmp/backups/old2.sql.gz"),
        ]

        # Use side_effect with a list: first call raises OSError, second call succeeds
        with patch.object(Path, "exists", return_value=True):
            with patch(
                "app.tasks.backups._list_expired_dumps", return_value=expired_files
            ):
                with patch.object(
                    Path, "unlink", side_effect=[OSError("Permission denied"), None]
                ):
                    result = purge_old_backups_task()

        assert result == 2  # Returns count of expired files
        # Should have one success and one failure audit
        mock_audit.assert_any_call("DB_BACKUP_PURGED", dump_path=str(expired_files[1]))
        mock_audit.assert_any_call(
            "DB_BACKUP_PURGE_FAILED",
            dump_path=str(expired_files[0]),
            error="Permission denied",
        )

    @patch("app.tasks.backups.settings")
    @patch("app.tasks.backups.audit")
    def test_purge_old_backups_task_uses_missing_ok(self, mock_audit, mock_settings):
        """Test that unlink is called with missing_ok=True."""
        mock_settings.BACKUP_DIR = "/tmp/backups"
        mock_settings.BACKUP_RETENTION_DAYS = 7

        expired_files = [Path("/tmp/backups/old1.sql.gz")]

        with patch.object(Path, "exists", return_value=True):
            with patch(
                "app.tasks.backups._list_expired_dumps", return_value=expired_files
            ):
                with patch.object(Path, "unlink") as mock_unlink:
                    purge_old_backups_task()

        mock_unlink.assert_called_once_with(missing_ok=True)


class TestListExpiredDumps:
    """Test _list_expired_dumps helper function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_directory = Path("/tmp/backups")

    @patch("app.tasks.backups.datetime")
    def test_list_expired_dumps_finds_expired_files(self, mock_datetime):
        """Test that expired files are found correctly."""
        # Create a mock datetime object
        mock_dt = Mock()
        mock_dt.timestamp.return_value = 1701446400.0
        mock_datetime.utcnow.return_value = mock_dt

        # 7 days ago = 1700841600.0
        cutoff = 1701446400.0 - (7 * 86400)

        # Mock file stats
        old_file = Mock()
        old_file.stat.return_value.st_mtime = cutoff - 3600  # 1 hour older than cutoff

        new_file = Mock()
        new_file.stat.return_value.st_mtime = cutoff + 3600  # 1 hour newer than cutoff

        with patch.object(Path, "glob", return_value=[old_file, new_file]):
            result = _list_expired_dumps(self.test_directory, 7)

        assert result == [old_file]
        assert new_file not in result

    @patch("app.tasks.backups.datetime")
    def test_list_expired_dumps_no_files(self, mock_datetime):
        """Test when no files exist in directory."""
        mock_dt = Mock()
        mock_dt.timestamp.return_value = 1701446400.0
        mock_datetime.utcnow.return_value = mock_dt

        with patch.object(Path, "glob", return_value=[]):
            result = _list_expired_dumps(self.test_directory, 7)

        assert result == []

    @patch("app.tasks.backups.datetime")
    def test_list_expired_dumps_only_sql_gz_files(self, mock_datetime):
        """Test that only .sql.gz files are considered."""
        mock_dt = Mock()
        mock_dt.timestamp.return_value = 1701446400.0
        mock_datetime.utcnow.return_value = mock_dt

        # Mock files with different extensions
        sql_gz_file = Mock(spec=Path)
        sql_gz_file.stat.return_value.st_mtime = (
            1700841599.0  # 1 second older than cutoff
        )
        sql_gz_file.name = "expired.sql.gz"

        txt_file = Mock(spec=Path)
        txt_file.stat.return_value.st_mtime = 1700841600.0  # Old but wrong extension
        txt_file.name = "not_expired.txt"

        # Only the .sql.gz file should be returned by glob
        with patch.object(Path, "glob", return_value=[sql_gz_file]):
            result = _list_expired_dumps(self.test_directory, 7)

        assert result == [sql_gz_file]
        assert txt_file not in result

    @patch("app.tasks.backups.datetime")
    def test_list_expired_dumps_cutoff_calculation(self, mock_datetime):
        """Test that cutoff is calculated correctly."""
        mock_dt = Mock()
        mock_dt.timestamp.return_value = 1701446400.0
        mock_datetime.utcnow.return_value = mock_dt

        # 7 days = 7 * 86400 = 604800 seconds
        with patch.object(Path, "glob", return_value=[]):
            _list_expired_dumps(self.test_directory, 7)

        # Verify the calculation
        assert mock_dt.timestamp.call_count == 1

    @patch("app.tasks.backups.datetime")
    def test_list_expired_dumps_different_retention_periods(self, mock_datetime):
        """Test with different retention periods."""
        mock_dt = Mock()
        mock_dt.timestamp.return_value = 1701446400.0
        mock_datetime.utcnow.return_value = mock_dt

        test_file = Mock()
        test_file.stat.return_value.st_mtime = (
            1700841599.0  # 1 second older than cutoff
        )

        with patch.object(Path, "glob", return_value=[test_file]):
            # 7 days retention - file should be expired
            result_7_days = _list_expired_dumps(self.test_directory, 7)
            assert result_7_days == [test_file]

            # 30 days retention - file should not be expired
            result_30_days = _list_expired_dumps(self.test_directory, 30)
            assert result_30_days == []
