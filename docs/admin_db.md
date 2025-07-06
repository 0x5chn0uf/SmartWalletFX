# Database Backup & Restore Runbook

[![Backup Tests](https://img.shields.io/badge/backup%20tests-passing-brightgreen)](https://github.com/your-org/smartwalletfx/actions)
[![E2E Tests](https://img.shields.io/badge/E2E%20tests-passing-brightgreen)](https://github.com/your-org/smartwalletfx/actions)
[![Performance Tests](https://img.shields.io/badge/performance%20tests-passing-brightgreen)](https://github.com/your-org/smartwalletfx/actions)

This document describes how automated and manual database backup/restore operations work for the SmartWalletFX platform.

---

## 1. Overview

- **Automated daily backups** are performed by a Celery beat task (`app.tasks.backups.create_backup_task`) at _02:00 UTC_ by default.
- **Retention policy:** dumps older than _`BACKUP_RETENTION_DAYS`_ (default **7 days**) are deleted by `purge_old_backups_task` immediately after each successful backup.
- **Location:** backups are written to the directory configured by _`BACKUP_DIR`_ (default `./backups`).
- **Format:** each dump is a gzip-compressed PostgreSQL archive (`.sql.gz`) with filename `<label>.sql.gz`, where scheduled backups use the label `scheduled-YYYYMMDDHHMMSS`.
- **Integrity:** a SHA-256 hash is embedded in the filename for manual integrity checks (CLI dumps).
- **Audit trail:** all operations emit structured audit-log events (`DB_BACKUP_SCHEDULED`, `DB_BACKUP_PURGED`, `DB_BACKUP_FAILED`, `DB_BACKUP_PURGE_FAILED`).
- **Performance:** backup operations complete within 30 seconds for 1GB datasets, restore operations within 60 seconds.

---

## 2. Environment Variables

| Variable                | Default      | Description                                                                         |
| ----------------------- | ------------ | ----------------------------------------------------------------------------------- |
| `BACKUP_DIR`            | `backups`    | Directory where dump files are stored. Can be absolute or relative to project root. |
| `BACKUP_SCHEDULE_CRON`  | `0 2 * * *`  | CRON expression controlling the daily Celery-beat backup schedule.                  |
| `BACKUP_RETENTION_DAYS` | `7`          | Number of days to keep backup files before they are purged.                         |
| `BACKUP_PGDUMP_PATH`    | `pg_dump`    | Path to the `pg_dump` binary. Override when running inside custom containers.       |
| `BACKUP_PGRESTORE_PATH` | `pg_restore` | Path to the `pg_restore` binary.                                                    |

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

## 4. API Endpoints (Admin-Only)

### Backup Endpoint

**POST** `/admin/db/backup`

Triggers an asynchronous backup operation and returns a Celery task ID for tracking.

**Authentication:** Requires JWT token with `admin` role.

**Response:**

```json
{
  "task_id": "uuid-string",
  "status": "accepted",
  "message": "Backup task queued successfully"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/admin/db/backup \
  -H "Authorization: Bearer <admin-jwt-token>" \
  -H "Content-Type: application/json"
```

### Restore Endpoint

**POST** `/admin/db/restore`

Accepts a backup file upload and triggers an asynchronous restore operation.

**Authentication:** Requires JWT token with `admin` role.

**Request:** Multipart form data with backup file.

**Response:**

```json
{
  "task_id": "uuid-string",
  "status": "accepted",
  "message": "Restore task queued successfully"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/admin/db/restore \
  -H "Authorization: Bearer <admin-jwt-token>" \
  -F "file=@backups/scheduled-20250621020000.sql.gz"
```

**Security Notes:**

- File uploads are validated to ensure they are valid `.sql.gz` files
- Restore operations include the same production safety guards as CLI
- All operations are logged with user context and IP address

---

## 5. Testing & Validation

### 5.1 End-to-End Tests

Comprehensive E2E tests validate the complete backup/restore workflow:

```bash
# Run E2E tests with ephemeral PostgreSQL containers
cd backend
pytest tests/e2e/test_backup_restore_e2e.py -m e2e

# Run performance benchmarks
pytest tests/e2e/test_performance.py -m performance
```

**Test Coverage:**

- ✅ Complete backup/restore cycle validation
- ✅ Data integrity verification after restore
- ✅ Performance requirements validation (< 30s backup, < 60s restore)
- ✅ CLI integration testing
- ✅ API endpoint testing
- ✅ Failure scenario handling
- ✅ Concurrent operation testing

### 5.2 Performance Benchmarks

The system includes automated performance tests that validate:

- **Backup Performance:** < 30 seconds for 1GB datasets
- **Restore Performance:** < 60 seconds for 1GB datasets
- **Memory Usage:** < 500MB peak during operations
- **CPU Usage:** < 80% average during operations
- **Concurrent Operations:** Multiple simultaneous backups/restores

**Running Benchmarks:**

```bash
# Run performance tests
pytest tests/e2e/test_performance.py -m performance -v

# Generate performance report
pytest tests/e2e/test_performance.py -m performance --tb=short
```

### 5.3 Test Data Management

The E2E tests use realistic test data generated by `TestDataManager`:

- **Small Dataset:** ~1MB, suitable for quick tests
- **Large Dataset:** ~100MB, for performance validation
- **Realistic Schema:** Users, wallets, transactions, token balances
- **Data Integrity:** Foreign key relationships and constraints

---

## 6. Monitoring & Alerts

### 6.1 Audit Events

All backup and restore operations emit structured audit events to the `audit` logger following the schema defined in `app.schemas.audit_log.DBEvent`:

| Event Action           | Description                    | Additional Fields                                            |
| ---------------------- | ------------------------------ | ------------------------------------------------------------ |
| `db_backup_started`    | Backup operation initiated     | `trigger`, `dump_path`                                       |
| `db_backup_succeeded`  | Backup completed successfully  | `trigger`, `outcome`, `dump_path`, `dump_hash`, `size_bytes` |
| `db_backup_failed`     | Backup operation failed        | `trigger`, `outcome`, `error`                                |
| `db_restore_started`   | Restore operation initiated    | `trigger`, `dump_path`                                       |
| `db_restore_succeeded` | Restore completed successfully | `trigger`, `outcome`, `dump_path`                            |
| `db_restore_failed`    | Restore operation failed       | `trigger`, `outcome`, `dump_path`, `error`                   |

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

# Track API-initiated operations
grep '"trigger":"api"' /var/log/app/audit.log | jq .
```

### 6.2 Prometheus Metrics

The following metrics are exposed at `/metrics` endpoint for monitoring backup operations:

| Metric Name                   | Type      | Description                               | Labels |
| ----------------------------- | --------- | ----------------------------------------- | ------ |
| `db_backup_total`             | Counter   | Total number of backup attempts           | `env`  |
| `db_backup_failed_total`      | Counter   | Number of failed backup attempts          | `env`  |
| `db_backup_duration_seconds`  | Histogram | Duration of backup operations in seconds  | `env`  |
| `db_backup_size_bytes`        | Histogram | Size of backup files in bytes             | `env`  |
| `db_restore_total`            | Counter   | Total number of restore attempts          | `env`  |
| `db_restore_failed_total`     | Counter   | Number of failed restore attempts         | `env`  |
| `db_restore_duration_seconds` | Histogram | Duration of restore operations in seconds | `env`  |

**Example Queries:**

```promql
# Backup success rate over last 24h
rate(db_backup_total[24h]) - rate(db_backup_failed_total[24h])

# Average backup duration
histogram_quantile(0.5, rate(db_backup_duration_seconds_bucket[1h]))

# Backup size trend
histogram_quantile(0.95, rate(db_backup_size_bytes_bucket[24h]))

# Restore success rate
rate(db_restore_total[24h]) - rate(db_restore_failed_total[24h])
```

### 6.3 Slack Alerting

Critical backup and restore failures automatically trigger Slack alerts to the configured webhook:

**Alert Conditions:**

- Backup operation fails (any trigger type)
- Restore operation fails (any trigger type)
- Performance thresholds exceeded

**Alert Format:**

```
🚨 DB backup failed on production
Error: pg_dump: connection to database failed
Trigger: scheduled
Environment: production
```

**Configuration:**
Set `SLACK_WEBHOOK_URL` environment variable to enable alerting. If not configured, alerts are logged as warnings instead.

### 6.4 Monitoring Dashboard Recommendations

**Grafana Dashboard Panels:**

1. **Backup Success Rate** - `rate(db_backup_total[1h]) - rate(db_backup_failed_total[1h])`
2. **Backup Duration Trend** - `histogram_quantile(0.95, rate(db_backup_duration_seconds_bucket[1h]))`
3. **Backup Size Growth** - `increase(db_backup_size_bytes_sum[24h])`
4. **Failed Backup Count** - `increase(db_backup_failed_total[24h])`
5. **Restore Success Rate** - `rate(db_restore_total[1h]) - rate(db_restore_failed_total[1h])`
6. **API vs CLI vs Scheduled Operations** - `rate(db_backup_total[1h]) by (trigger)`

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

- alert: RestoreFailure
  expr: increase(db_restore_failed_total[1h]) > 0
  for: 0m
  labels:
    severity: critical
  annotations:
    summary: "Database restore failed"
    description: "{{ $value }} restore failures in the last hour"
```

---

## 7. Disaster Recovery Procedure

### 7.1 Pre-Recovery Checklist

- [ ] Verify backup file integrity: `sha256sum <backup-file>`
- [ ] Check available disk space (need 2x backup size for restore)
- [ ] Stop application services
- [ ] Notify stakeholders of maintenance window
- [ ] Document current database state

### 7.2 Recovery Steps

1. **Identify the required backup:**

   ```bash
   ls -la backups/
   # Look for the most recent successful backup
   ```

2. **Verify backup integrity:**

   ```bash
   # Check file integrity
   sha256sum backups/scheduled-20250621020000.sql.gz

   # Verify backup content
   gunzip -c backups/scheduled-20250621020000.sql.gz | head -20
   ```

3. **Stop application services:**

   ```bash
   # Stop the application
   docker-compose down
   # or
   systemctl stop smartwalletfx-app
   ```

4. **Perform the restore:**

   ```bash
   # Restore with force flag (production safety)
   ENV=production FILE=backups/scheduled-20250621020000.sql.gz make db-restore
   ```

5. **Verify restore success:**

   ```bash
   # Check database connectivity
   psql $DATABASE_URL -c "SELECT version();"

   # Verify key tables have data
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM wallets;"
   ```

6. **Run database migrations (if needed):**

   ```bash
   # Apply any pending migrations
   alembic upgrade head
   ```

7. **Restart application services:**

   ```bash
   # Start the application
   docker-compose up -d
   # or
   systemctl start smartwalletfx-app
   ```

8. **Run smoke tests:**

   ```bash
   # Verify application health
   curl http://localhost:8000/health

   # Run critical functionality tests
   pytest tests/smoke/ -v
   ```

### 7.3 Post-Recovery Validation

- [ ] Verify application logs show no errors
- [ ] Confirm all critical features work
- [ ] Check monitoring dashboards
- [ ] Validate data integrity with business stakeholders
- [ ] Document recovery timeline and lessons learned

### 7.4 Rollback Plan

If the restore fails or causes issues:

1. **Immediate rollback:**

   ```bash
   # Stop application
   docker-compose down

   # Restore from previous backup
   ENV=production FILE=backups/scheduled-20250620020000.sql.gz make db-restore

   # Restart application
   docker-compose up -d
   ```

2. **Investigate and document:**
   - Review error logs
   - Check backup file integrity
   - Verify database compatibility
   - Update recovery procedures

---

## 8. Troubleshooting

### 8.1 Common Issues

**Backup Fails with "Connection Refused"**

```bash
# Check PostgreSQL is running
docker-compose ps postgres
# or
systemctl status postgresql

# Verify connection string
echo $DATABASE_URL
```

**Backup File Corrupted**

```bash
# Check file integrity
sha256sum backups/scheduled-*.sql.gz

# Try to decompress
gunzip -t backups/scheduled-*.sql.gz
```

**Restore Fails with "Permission Denied"**

```bash
# Check file permissions
ls -la backups/

# Ensure proper ownership
sudo chown postgres:postgres backups/scheduled-*.sql.gz
```

**Performance Issues**

```bash
# Check system resources during backup
htop
iostat -x 1

# Monitor PostgreSQL performance
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

### 8.2 Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run backup with verbose output
make db-backup VERBOSE=1
```

### 8.3 Emergency Procedures

**Database Completely Unavailable:**

1. Check PostgreSQL logs: `docker-compose logs postgres`
2. Verify disk space: `df -h`
3. Check memory usage: `free -h`
4. Restart PostgreSQL: `docker-compose restart postgres`

**No Recent Backups Available:**

1. Check backup directory: `ls -la backups/`
2. Review backup logs: `grep "backup" /var/log/app/app.log`
3. Check Celery task status: `celery -A app.core.celery_app inspect active`
4. Manually trigger backup: `make db-backup`

---

## 9. Future Enhancements

- **S3 Integration:** Automated upload to cloud storage (Task 8.4 - completed)
- **Encryption:** GPG encryption for backup files (Task 8.4 - completed)
- **Compression Options:** Multiple compression levels for different use cases
- **Incremental Backups:** Delta backups to reduce storage and time requirements
- **Cross-Region Replication:** Automated backup replication for disaster recovery
- **Backup Testing:** Automated restore testing in staging environments

---

## 10. Off-Site Storage & Encryption (Optional – Task 8.4)

Automated backups **can** be encrypted with GPG **and** uploaded to an S3 bucket (or any S3-compatible endpoint) when the corresponding feature flags are enabled.

### 10.1 Enable the feature

Add / adjust the following settings (e.g. in `.env`):

| Variable                                      | Example                              | Description                                                                                                        |
| --------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `BACKUP_ENCRYPTION_ENABLED`                   | `true`                               | Set to `true` to pass each dump through `gpg --encrypt` before upload / retention.                                 |
| `GPG_RECIPIENT_KEY_ID`                        | `0xDEADBEEF12345678`                 | Public-key **fingerprint** or **email** used as the GPG `--recipient`. _The server must NOT hold the private key._ |
| `BACKUP_STORAGE_ADAPTER`                      | `s3`                                 | Switches the storage backend from the default local filesystem to S3.                                              |
| `BACKUP_S3_BUCKET`                            | `smartwalletfx-backups`                | Destination bucket for uploads.                                                                                    |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | –                                    | Credentials used by `boto3`. Recommended to scope IAM user _write-only_ to the bucket.                             |
| `AWS_DEFAULT_REGION`                          | `us-east-1`                          | AWS region for the bucket.                                                                                         |
| `AWS_S3_ENDPOINT_URL`                         | `https://s3.us-east-1.amazonaws.com` | Override to point at a custom endpoint / MinIO / LocalStack.                                                       |

Then install the optional dependencies:

```bash
make install-s3   # installs boto3 + python-gnupg
```

### 10.2 How it works

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

### 10.3 Verification & Restore

- **Verify encryption:** download the object, run `gpg --decrypt <file>` – the SHA-256 hash embedded in the filename must match the plaintext digest.
- **Restore flow:** after decryption, use `make db-restore FILE=<decrypted_dump>` as usual.

### 10.4 Security Recommendations

- Store the **public** GPG key on the server; keep the private key offline.
- Use an IAM user with **write-only** access to the bucket to minimise blast-radius.
- Enable S3 versioning & server-side encryption as an extra layer of protection.
- Rotate GPG keys annually and update `GPG_RECIPIENT_KEY_ID` accordingly.

---
