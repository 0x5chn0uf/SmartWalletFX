"""Database backup & restore helpers.

Provides a framework-agnostic interface around ``pg_dump`` and
``pg_restore`` for creating and restoring PostgreSQL logical dumps.
Backups can be compressed, hashed, optionally encrypted and uploaded to
remote storage. Structured audit logs and Prometheus metrics accompany
each operation.

Exported API:

* ``create_dump(...) -> pathlib.Path``
* ``restore_dump(...) -> None``

Domain-level exceptions:

* ``BackupError``
* ``RestoreError``
"""
from __future__ import annotations

import gzip
import hashlib
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Final, Optional, Sequence

from app.core.config import settings
from app.schemas.audit_log import DBEvent
from app.storage import get_storage_adapter
from app.utils import metrics
from app.utils.encryption import EncryptionError, encrypt_file
from app.utils.logging import Audit

__all__: Final[Sequence[str]] = (
    "BackupError",
    "RestoreError",
    "create_dump",
    "restore_dump",
)


class BackupError(RuntimeError):
    """Raised when a database backup fails."""


class RestoreError(RuntimeError):
    """Raised when restoring from a backup fails."""


# ---------------------------------------------------------------------------
# Public helper functions (stubs – to be implemented in 8.1.2)
# ---------------------------------------------------------------------------


def _resolve_dsn(env: Optional[Dict[str, str]] = None) -> str:
    """Return DATABASE_URL from *env* or process environment.

    Raises KeyError if not found (caller should handle or allow to propagate)."""

    return (env or os.environ)["DATABASE_URL"]


def build_pg_dump_cmd(
    output_dir: Path,
    *,
    label: Optional[str] = None,
    compress: bool = True,
    dsn: Optional[str] = None,
    pg_dump_path: str = "pg_dump",
) -> list[str]:
    """Construct an arg-list for *pg_dump*.

    Notes
    -----
    • We always use *custom* format ("-Fc") because it supports parallel
      restore, compression, and is version-portable.
    • No shell metacharacters are introduced; caller should pass the resulting
      list to :pyfunc:`subprocess.run` with *shell=False*.
    """
    if not output_dir.exists():
        raise FileNotFoundError(output_dir)

    basename = (label or datetime.utcnow().strftime("%Y%m%dT%H%M%S")) + ".dump"
    dump_path = output_dir / basename

    cmd = [
        pg_dump_path,
        "--format",
        "custom",
        "--file",
        str(dump_path),
    ]

    # Compression level is handled automatically by custom format; the *compress*
    # flag will later trigger *gzip* wrapping in create_dump().  For the command
    # builder we simply ignore it.

    cmd.append(dsn or _resolve_dsn())

    return cmd


def build_pg_restore_cmd(
    dump_path: Path,
    *,
    target_db_url: Optional[str] = None,
    pg_restore_path: str = "pg_restore",
) -> list[str]:
    """Construct arg-list for *pg_restore* using sensible defaults."""

    if not dump_path.exists():
        raise FileNotFoundError(dump_path)

    cmd = [
        pg_restore_path,
        "--clean",  # drop existing objects before recreating
        "--if-exists",
        "--no-owner",
        "--dbname",
        target_db_url or _resolve_dsn(),
        str(dump_path),
    ]
    return cmd


def _hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return SHA-256 hex digest of *path* contents."""

    sha256 = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _compress_and_hash(dump_path: Path) -> tuple[Path, str]:
    """Compress *dump_path* with gzip and return (compressed_path, sha256_hex).

    The resulting filename is `<timestamp>_<hash8>.sql.gz` where *hash8* is the
    first eight characters of the SHA-256 digest calculated **before**
    compression (so the hash validates logical dump integrity regardless of
    compression differences).
    """
    if not dump_path.exists():
        raise FileNotFoundError(dump_path)

    # Compute hash before compression so verification does not depend on gzip
    # metadata such as mtime.
    digest = _hash_file(dump_path)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    compressed_name = f"{ts}_{digest[:8]}.sql.gz"
    compressed_path = dump_path.with_name(compressed_name)

    # Gzip-compress
    with dump_path.open("rb") as src, gzip.open(
        compressed_path, "wb", compresslevel=9
    ) as dst:
        shutil.copyfileobj(src, dst)

    # Remove original uncompressed dump to save space
    dump_path.unlink(missing_ok=False)

    return compressed_path, digest


def _run_subprocess(
    cmd: list[str], *, env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess:  # pragma: no cover
    """Thin wrapper around subprocess.run allowing easier monkey-patching in tests."""

    return subprocess.run(
        cmd, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


# ---------------------------------------------------------------------------
# Public API implementations (partial – will be expanded in future sub-tasks)
# ---------------------------------------------------------------------------


def create_dump(
    output_dir: Path,
    *,
    compress: bool = True,
    label: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    trigger: str = "manual",
) -> Path:  # noqa: C901
    """Create a logical PostgreSQL dump and return the path to the dump file.

    Emits an audit log regardless of success/failure.
    """
    cmd = build_pg_dump_cmd(output_dir, label=label, compress=compress)
    # Extract dump file path from command list (value after --file)
    try:
        file_idx = cmd.index("--file") + 1
        dump_path = Path(cmd[file_idx])
    except (ValueError, IndexError):
        # Should never happen given builder invariant
        raise BackupError("dump path not found in pg_dump command") from None

    # Metrics & audit start
    Audit.log_structured_audit_event(
        DBEvent(
            action="db_backup_started",
            timestamp=datetime.now(timezone.utc),
            trigger=trigger,
            dump_path=str(dump_path),
        )
    )
    metrics.BACKUP_TOTAL_L.inc()
    _t0 = time.perf_counter()

    try:
        _run_subprocess(cmd, env=env)

        final_path = dump_path
        sha256_digest = None
        if compress:
            final_path, sha256_digest = _compress_and_hash(dump_path)
        else:
            sha256_digest = _hash_file(dump_path)

        # Optional encryption
        if settings.BACKUP_ENCRYPTION_ENABLED:
            try:
                encrypted_path = encrypt_file(final_path)
                final_path = encrypted_path
                Audit.log_structured_audit_event(
                    DBEvent(
                        action="db_backup_encrypted",
                        timestamp=datetime.now(timezone.utc),
                        trigger=trigger,
                        dump_path=str(final_path),
                    )
                )
            except EncryptionError as exc:
                Audit.log_structured_audit_event(
                    DBEvent(
                        action="db_backup_encrypt_failed",
                        timestamp=datetime.now(timezone.utc),
                        trigger=trigger,
                        dump_path=str(final_path),
                        outcome="failure",
                        error=str(exc),
                    )
                )
                raise BackupError("encryption failed") from exc

        # Optional remote storage upload
        try:
            adapter = get_storage_adapter()
            remote_id = adapter.save(final_path, destination=final_path.name)
            Audit.log_structured_audit_event(
                DBEvent(
                    action="db_backup_uploaded",
                    timestamp=datetime.now(timezone.utc),
                    trigger=trigger,
                    dump_path=str(final_path),
                    remote_id=remote_id,
                )
            )
        except Exception as exc:
            Audit.log_structured_audit_event(
                DBEvent(
                    action="db_backup_upload_failed",
                    timestamp=datetime.now(timezone.utc),
                    trigger=trigger,
                    dump_path=str(final_path),
                    outcome="failure",
                    error=str(exc),
                )
            )
            # We do *not* fail the backup if upload fails; local dump remains valid

        # Success metrics
        duration = time.perf_counter() - _t0
        metrics.BACKUP_DURATION_SECONDS_L.observe(duration)
        metrics.BACKUP_SIZE_BYTES_L.observe(final_path.stat().st_size)

        Audit.log_structured_audit_event(
            DBEvent(
                action="db_backup_succeeded",
                timestamp=datetime.now(timezone.utc),
                trigger=trigger,
                outcome="success",
                dump_path=str(final_path),
                dump_hash=sha256_digest,
                size_bytes=final_path.stat().st_size,
            )
        )
        return final_path

    except Exception as exc:
        # Metrics & audit end
        duration = time.perf_counter() - _t0
        metrics.BACKUP_DURATION_SECONDS_L.observe(duration)
        metrics.BACKUP_FAILED_TOTAL_L.inc()

        Audit.log_structured_audit_event(
            DBEvent(
                action="db_backup_failed",
                timestamp=datetime.now(timezone.utc),
                trigger=trigger,
                outcome="failure",
                dump_path=str(dump_path),
                error=str(exc),
            )
        )
        raise BackupError("backup failed") from exc


def restore_dump(
    dump_path: Path,
    *,
    force: bool = False,
    target_db_url: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    trigger: str = "manual",
) -> None:
    """Restore a database dump from *dump_path*.

    Emits an audit log regardless of success/failure.
    """
    if settings.ENVIRONMENT == "production" and not force:
        raise RestoreError("cannot restore on production without --force flag")

    if not dump_path.exists():
        raise RestoreError(f"dump file not found: {dump_path}")

    Audit.log_structured_audit_event(
        DBEvent(
            action="db_restore_started",
            timestamp=datetime.now(timezone.utc),
            trigger=trigger,
            dump_path=str(dump_path),
        )
    )
    _t0 = time.perf_counter()
    cmd = build_pg_restore_cmd(dump_path, target_db_url=target_db_url)
    try:
        _run_subprocess(cmd, env=env)
        duration = time.perf_counter() - _t0
        Audit.log_structured_audit_event(
            DBEvent(
                action="db_restore_succeeded",
                timestamp=datetime.now(timezone.utc),
                trigger=trigger,
                outcome="success",
                dump_path=str(dump_path),
            )
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        # Metrics & audit end
        duration = time.perf_counter() - _t0
        metrics.BACKUP_DURATION_SECONDS_L.observe(duration)
        metrics.BACKUP_FAILED_TOTAL_L.inc()

        Audit.log_structured_audit_event(
            DBEvent(
                action="db_restore_failed",
                timestamp=datetime.now(timezone.utc),
                trigger=trigger,
                outcome="failure",
                dump_path=str(dump_path),
                error=str(exc),
            )
        )

        raise RestoreError("restore failed") from exc
