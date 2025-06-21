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

### 5.1 Audit Events
All backup and restore operations emit structured audit events to the `audit` logger following the schema defined in `app.schemas.audit_log.DBEvent`:

| Event Action | Description | Additional Fields |
|--------------|-------------|-------------------|
| `db_backup_started` | Backup operation initiated | `trigger`, `dump_path` |
| `db_backup_succeeded` | Backup completed successfully | `trigger`, `outcome`, `dump_path`, `dump_hash`, `size_bytes` |
| `db_backup_failed` | Backup operation failed | `trigger`, `outcome`, `error` |
| `db_restore_started` | Restore operation initiated | `trigger`, `dump_path` |
| `db_restore_succeeded` | Restore completed successfully | `trigger`, `outcome`, `dump_path` |
| `db_restore_failed` | Restore operation failed | `trigger`, `outcome`, `dump_path`, `error` |

**Context Fields:**
- `trigger`: How the operation was initiated (`api`, `cli`, `scheduled`)
- `user_id`: Authenticated user ID (when triggered via API)
- `ip_address`: Source IP address (when triggered via API)
- `trace_id`: Request correlation ID for tracking

**Search Examples:**
```bash
# Find all backup failures in the last 24h
grep '"action":"db_backup_failed"' /var/log/app/audit.log | jq .

# Monitor scheduled backup success
grep '"trigger":"scheduled"' /var/log/app/audit.log | grep '"outcome":"success"'
```

### 5.2 Prometheus Metrics
The following metrics are exposed at `/metrics` endpoint for monitoring backup operations:

| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `db_backup_total` | Counter | Total number of backup attempts | `env` |
| `db_backup_failed_total` | Counter | Number of failed backup attempts | `env` |
| `db_backup_duration_seconds` | Histogram | Duration of backup operations in seconds | `env` |
| `db_backup_size_bytes` | Histogram | Size of backup files in bytes | `env` |

**Example Queries:**
```promql
# Backup success rate over last 24h
rate(db_backup_total[24h]) - rate(db_backup_failed_total[24h])

# Average backup duration
histogram_quantile(0.5, rate(db_backup_duration_seconds_bucket[1h]))

# Backup size trend
histogram_quantile(0.95, rate(db_backup_size_bytes_bucket[24h]))
```

### 5.3 Slack Alerting
Critical backup and restore failures automatically trigger Slack alerts to the configured webhook:

**Alert Conditions:**
- Backup operation fails (any trigger type)
- Restore operation fails (any trigger type)

**Alert Format:**
```
🚨 DB backup failed on production
Error: pg_dump: connection to database failed
```

**Configuration:**
Set `SLACK_WEBHOOK_URL` environment variable to enable alerting. If not configured, alerts are logged as warnings instead.

### 5.4 Monitoring Dashboard Recommendations
**Grafana Dashboard Panels:**
1. **Backup Success Rate** - `rate(db_backup_total[1h]) - rate(db_backup_failed_total[1h])`
2. **Backup Duration Trend** - `histogram_quantile(0.95, rate(db_backup_duration_seconds_bucket[1h]))`
3. **Backup Size Growth** - `increase(db_backup_size_bytes_sum[24h])`
4. **Failed Backup Count** - `increase(db_backup_failed_total[24h])`

**Alertmanager Rules:**
```yaml
- alert: BackupFailure
  expr: increase(db_backup_failed_total[1h]) > 0
  for: 0m
  labels:
    severity: critical
  annotations:
    summary: "Database backup failed"
    description: "{{ $value }} backup failures in the last hour"

- alert: BackupDurationHigh
  expr: histogram_quantile(0.95, rate(db_backup_duration_seconds_bucket[1h])) > 300
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Backup taking too long"
    description: "95th percentile backup duration is {{ $value }}s"
```

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

## 8. Off-Site Storage & Encryption (Optional – Task 8.4)

Automated backups **can** be encrypted with GPG **and** uploaded to an S3 bucket (or any S3-compatible endpoint) when the corresponding feature flags are enabled.

### 8.1 Enable the feature

Add / adjust the following settings (e.g. in `.env`):

| Variable | Example | Description |
|----------|---------|-------------|
| `BACKUP_ENCRYPTION_ENABLED` | `true` | Set to `true` to pass each dump through `gpg --encrypt` before upload / retention. |
| `GPG_RECIPIENT_KEY_ID` | `0xDEADBEEF12345678` | Public-key **fingerprint** or **email** used as the GPG `--recipient`. *The server must NOT hold the private key.* |
| `BACKUP_STORAGE_ADAPTER` | `s3` | Switches the storage backend from the default local filesystem to S3. |
| `BACKUP_S3_BUCKET` | `trading-bot-backups` | Destination bucket for uploads. |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | – | Credentials used by `boto3`. Recommended to scope IAM user *write-only* to the bucket. |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region for the bucket. |
| `AWS_S3_ENDPOINT_URL` | `https://s3.us-east-1.amazonaws.com` | Override to point at a custom endpoint / MinIO / LocalStack. |

Then install the optional dependencies:
```bash
make install-s3   # installs boto3 + python-gnupg
```

### 8.2 How it works

1. `create_backup_task` (or CLI) produces a logical dump file.
2. If `BACKUP_ENCRYPTION_ENABLED=true`, the file is encrypted via:
   ```bash
   gpg --encrypt --recipient "$GPG_RECIPIENT_KEY_ID" dump.sql.gz
   ```
   The original plaintext dump is **not** removed until successful encryption.
3. The active `StorageAdapter` is resolved:
   ```python
   adapter = get_storage_adapter()  # "local" or "s3"
   adapter.save(encrypted_path)
   ```
4. On S3 upload success, an audit event `DB_BACKUP_UPLOADED` is emitted with the S3 key.

### 8.3 Verification & Restore

* **Verify encryption:** download the object, run `gpg --decrypt <file>` – the SHA-256 hash embedded in the filename must match the plaintext digest.
* **Restore flow:** after decryption, use `make db-restore FILE=<decrypted_dump>` as usual.

### 8.4 Security Recommendations

* Store the **public** GPG key on the server; keep the private key offline.
* Use an IAM user with **write-only** access to the bucket to minimise blast-radius.
* Enable S3 versioning & server-side encryption as an extra layer of protection.
* Rotate GPG keys annually and update `GPG_RECIPIENT_KEY_ID` accordingly.

--- 