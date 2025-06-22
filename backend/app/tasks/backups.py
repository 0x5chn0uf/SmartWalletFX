from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List

from celery import shared_task
from celery.schedules import (  # noqa: F401  # used by Celery beat when inspecting task
    crontab,
)

from app.core.config import settings
from app.utils.db_backup import (  # noqa: E501 – heavy logic lives in utils module
    create_dump,
    restore_dump,
)
from app.utils.logging import audit

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.backups.create_backup_task")
def create_backup_task() -> str:
    """Celery task: trigger `pg_dump` via the high-level helper.

    Returns the path of the created dump file so that chain / chord
    workflows (or simple .delay().get()) can reference the artifact.
    """

    output_dir = Path(settings.BACKUP_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use UTC timestamp to ensure deterministic filenames across nodes.
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    label = f"scheduled-{timestamp}"
    try:
        dump_path = create_dump(output_dir=output_dir, label=label)
        audit(
            "DB_BACKUP_SCHEDULED",
            dump_path=str(dump_path),
            label=label,
        )

        # Trigger retention cleanup asynchronously (fire-and-forget)
        purge_old_backups_task.delay()
        return str(dump_path)
    except Exception as exc:  # pragma: no cover – let Celery capture traceback
        audit("DB_BACKUP_FAILED", label=label)
        raise exc


@shared_task(name="app.tasks.backups.restore_from_upload_task")
def restore_from_upload_task(temp_file_path: str) -> str:
    """Celery task: restore database from uploaded backup file.

    Args:
        temp_file_path: Path to the temporary uploaded file

    Returns:
        Status message indicating completion
    """

    try:
        # Restore the database using the uploaded file
        restore_dump(Path(temp_file_path), force=True)

        audit(
            "DB_RESTORE_COMPLETED",
            dump_path=temp_file_path,
        )

        return f"Database restored successfully from {temp_file_path}"

    except Exception as exc:  # pragma: no cover
        audit("DB_RESTORE_FAILED", dump_path=temp_file_path, error=str(exc))
        raise exc
    finally:
        # Clean up the temporary file
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        except Exception as cleanup_exc:
            logger.warning(
                f"Failed to clean up temp file {temp_file_path}: {cleanup_exc}"
            )


def _list_expired_dumps(directory: Path, days: int) -> List[Path]:
    """Return dump files older than *days* days inside *directory*."""

    cutoff = datetime.utcnow().timestamp() - days * 86400
    expired: List[Path] = []
    for file_path in directory.glob("*.sql.gz"):
        if file_path.stat().st_mtime < cutoff:
            expired.append(file_path)
    return expired


@shared_task(name="app.tasks.backups.purge_old_backups_task")
def purge_old_backups_task() -> int:
    """Delete dumps older than *BACKUP_RETENTION_DAYS* and return count."""

    output_dir = Path(settings.BACKUP_DIR)
    if not output_dir.exists():
        return 0

    expired = _list_expired_dumps(output_dir, settings.BACKUP_RETENTION_DAYS)
    for file_path in expired:
        try:
            file_path.unlink(missing_ok=True)
            audit("DB_BACKUP_PURGED", dump_path=str(file_path))
        except Exception as exc:  # pragma: no cover
            audit("DB_BACKUP_PURGE_FAILED", dump_path=str(file_path), error=str(exc))
    return len(expired)
