# Database Backup & Restore Runbook

This document describes how automated and manual database backup/restore operations work for the trading-bot platform.

---

## 1. Overview

* **Automated daily backups** are performed by a Celery beat task (`app.tasks.backups.create_backup_task`) at *02:00 UTC* by default.
* **Retention policy:** dumps older than *`BACKUP_RETENTION_DAYS`* (default **7 days**) are deleted by `purge_old_backups_task` immediately after each successful backup.
* **Location:** backups are written to the directory configured by *`BACKUP_DIR`* (default `./backups`).
* **Format:** each dump is a gzip-compressed PostgreSQL archive (`.sql.gz`) with filename `<label>.sql.gz`, where scheduled backups use the label `scheduled-YYYYMMDDHHMMSS`.
* **Integrity:** a SHA-256 hash is embedded in the filename for manual integrity checks (CLI dumps).
* **Audit trail:** all operations emit structured audit-log events (`DB_BACKUP_SCHEDULED`, `DB_BACKUP_PURGED`, `DB_BACKUP_FAILED`, `DB_BACKUP_PURGE_FAILED`).

---

## 2. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_DIR` | `backups` | Directory where dump files are stored. Can be absolute or relative to project root. |
| `BACKUP_SCHEDULE_CRON` | `0 2 * * *` | CRON expression controlling the daily Celery-beat backup schedule. |
| `BACKUP_RETENTION_DAYS` | `7` | Number of days to keep backup files before they are purged. |
| `BACKUP_PGDUMP_PATH` | `pg_dump` | Path to the `pg_dump` binary. Override when running inside custom containers. |
| `BACKUP_PGRESTORE_PATH` | `pg_restore` | Path to the `pg_restore` binary. |

Add these to your **.env** file (or export in the deployment environment) to override defaults.

---

## 3. Manual Operations (CLI)

### Create Backup
```bash
make db-backup               # uses BACKUP_DIR & timestamped label
# or customise
BACKUP_DIR=/var/dumps LABEL=pre-migration make db-backup
```

### Restore Backup
```bash
# NEVER run on production without --force
FILE=backups/scheduled-20250621020000.sql.gz make db-restore
```
Safety guards prevent accidental restores in production unless `ENV=production` **and** the `--force` flag is supplied.

---

## 4. API Endpoints (admin-only – upcoming)
* `POST /admin/db/backup` – enqueues a backup task, returns Celery task ID.
* `POST /admin/db/restore` – accepts multipart upload or filename reference. _(Not yet implemented – tracked in Task 8.5.)_

---

## 5. Monitoring & Alerts

* **Audit logs**: Search for `action:DB_BACKUP_*` in Loki / Datadog.
* **Prometheus** metrics (future): `db_backup_success_total`, `db_backup_purge_total`, `db_backup_failure_total`.
* **Slack alerts**: backup failures trigger `#alerts-infra` via existing alerting pipeline.

---

## 6. Disaster-Recovery Procedure

1. Identify the required dump file in `BACKUP_DIR` or S3 (future enhancement).
2. Stop the application (maintenance mode) if restoring to production.
3. Run `make db-restore FILE=<dump>` **with extreme caution**.
4. Verify integrity, run migrations if required, and restart application.
5. Monitor logs and run smoke tests.

---

## 7. Future Work

* S3 upload & encryption pipeline (Task 8.4).
* Admin API endpoints for self-service backup/restore (Task 8.5).
* Prometheus metrics exporter (Task 8.6 view).
* Nightly CI job attaching latest dump as artefact for quick download by ops. 