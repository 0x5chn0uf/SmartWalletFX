import subprocess
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.audit_log import DBEvent
from app.utils.db_backup import BackupError, create_dump


@pytest.fixture
def mock_output_dir(tmp_path: Path) -> Path:
    """Provides a temporary directory for backup dumps."""
    return tmp_path


@patch("app.utils.db_backup.metrics")
@patch("app.utils.db_backup.get_storage_adapter")
@patch("app.utils.db_backup.encrypt_file")
@patch("app.utils.db_backup._run_subprocess")
@patch("app.utils.db_backup.log_structured_audit_event")
def test_create_dump_success_emits_correct_audit_logs(
    mock_log_event: MagicMock,
    mock_run_subprocess: MagicMock,
    mock_encrypt_file: MagicMock,
    mock_get_storage_adapter: MagicMock,
    mock_metrics: MagicMock,
    mock_output_dir: Path,
    monkeypatch,
):
    # Arrange
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost:5432/db")
    mock_run_subprocess.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=b"", stderr=b""
    )
    # Create a dummy file that pg_dump would have created
    dump_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + ".dump"
    (mock_output_dir / dump_name).touch()

    # Act
    create_dump(mock_output_dir, trigger="test")

    # Assert
    assert mock_log_event.call_count >= 2

    # Check the "started" event
    started_event_call = mock_log_event.call_args_list[0]
    started_event: DBEvent = started_event_call.args[0]
    assert isinstance(started_event, DBEvent)
    assert started_event.action == "db_backup_started"
    assert started_event.trigger == "test"

    # Check the "succeeded" event
    succeeded_event_call = mock_log_event.call_args_list[-1]
    succeeded_event: DBEvent = succeeded_event_call.args[0]
    assert isinstance(succeeded_event, DBEvent)
    assert succeeded_event.action == "db_backup_succeeded"
    assert succeeded_event.outcome == "success"
    assert succeeded_event.trigger == "test"
    assert succeeded_event.dump_hash is not None


@patch("app.utils.db_backup.metrics")
@patch("app.utils.db_backup._run_subprocess")
@patch("app.utils.db_backup.log_structured_audit_event")
def test_create_dump_failure_emits_correct_audit_log(
    mock_log_event: MagicMock,
    mock_run_subprocess: MagicMock,
    mock_metrics: MagicMock,
    mock_output_dir: Path,
    monkeypatch,
):
    # Arrange
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost:5432/db")
    mock_run_subprocess.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="pg_dump"
    )
    # Create a dummy file that pg_dump would have created
    dump_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + ".dump"
    (mock_output_dir / dump_name).touch()

    # Act & Assert
    with pytest.raises(BackupError):
        create_dump(mock_output_dir, trigger="test_failure")

    assert mock_log_event.call_count == 2

    # Check the "failed" event
    failed_event_call = mock_log_event.call_args_list[-1]
    failed_event: DBEvent = failed_event_call.args[0]
    assert isinstance(failed_event, DBEvent)
    assert failed_event.action == "db_backup_failed"
    assert failed_event.outcome == "failure"
    assert failed_event.trigger == "test_failure"
    assert "pg_dump" in failed_event.error
