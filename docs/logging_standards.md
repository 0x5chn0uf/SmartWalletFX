# Logging Standards & Audit Events

This document defines the project-wide conventions for **structured JSON logging** and, in particular, the _audit_ event format enforced by Subtask 4.16.

## 1 Log Categories

| Logger name      | Purpose                                                | Format                                                            |
| ---------------- | ------------------------------------------------------ | ----------------------------------------------------------------- |
| `uvicorn.access` | HTTP access logs emitted by the ASGI server            | Plain-text (left as default; parsed by Ingest pipeline)           |
| `app` (root)     | Application diagnostic logs                            | JSON via `structlog`                                              |
| `audit`          | _Security-grade_ events required for compliance / SIEM | JSON – **MUST** conform to the schemas in `app.schemas.audit_log` |

## 2 Audit Event Schema (v1)

Every audit record **MUST** include the following canonical fields; additional keys are allowed and schema-validated under `extra="allow"`:

| Field       | Type              | Description                                                       |
| ----------- | ----------------- | ----------------------------------------------------------------- | -------------------------------------------------- |
| `id`        | `str` (uuid4-hex) | Unique identifier for the log line (correlates multi-line events) |
| `timestamp` | ISO-8601 UTC      | Event creation time                                               |
| `action`    | `str`             | Machine-readable event name, e.g. `user_login_success`            |
| `trace_id`  | `str              | null`                                                             | Request correlation id (propagated via middleware) |

Concrete subclasses add their own required keys, e.g. `AuthEvent.result`, `DBEvent.outcome` etc.

### 2.1 Database Event Schema (DBEvent)

Database backup and restore operations emit `DBEvent` records with the following additional fields:

| Field        | Type  | Description                                               |
| ------------ | ----- | --------------------------------------------------------- | ------------------------------------------------------------------- |
| `trigger`    | `str` | How the event was triggered: `api`, `cli`, or `scheduled` |
| `outcome`    | `str  | null`                                                     | Final result: `success` or `failure` (null for intermediate events) |
| `dump_path`  | `str  | null`                                                     | Path to the backup dump file                                        |
| `dump_hash`  | `str  | null`                                                     | SHA256 hash of the dump file (alias: `sha256`)                      |
| `size_bytes` | `int  | null`                                                     | Size of the dump file in bytes                                      |
| `user_id`    | `str  | null`                                                     | Authenticated user ID when triggered via API                        |
| `ip_address` | `str  | null`                                                     | Source IP address when triggered via API                            |
| `error`      | `str  | null`                                                     | Error message for failed operations                                 |

**Example DBEvent Actions:**

- `db_backup_started` - Backup operation initiated
- `db_backup_succeeded` - Backup completed successfully
- `db_backup_failed` - Backup operation failed
- `db_restore_started` - Restore operation initiated
- `db_restore_succeeded` - Restore completed successfully
- `db_restore_failed` - Restore operation failed

**Sample DBEvent:**

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-06-22T14:30:00.123Z",
  "action": "db_backup_succeeded",
  "trace_id": "req_abc123",
  "trigger": "scheduled",
  "outcome": "success",
  "dump_path": "/backups/scheduled-20250622143000.sql.gz",
  "dump_hash": "sha256:a1b2c3d4...",
  "size_bytes": 1048576,
  "user_id": null,
  "ip_address": null
}
```

The authoritative schema lives in `backend/app/schemas/audit_log.py`. A machine-readable JSON Schema representation is exportable via:

```python
from app.schemas.audit_log import audit_json_schema
print(audit_json_schema())
```

## 3 Validation Pipeline

1. **Runtime** — Every call to `app.utils.logging.audit()` injects mandatory keys and _then_ passes the payload to `validate_audit_event()`. Behaviour is tuned via `AUDIT_VALIDATION` env-var:
   • `hard` (default in tests) → raise on validation failure  
   • `warn` → emit `warnings.warn` but continue  
   • `off` → skip validation (perf mode)
2. **Tests** — A pytest plugin (`tests.plugins.audit_validator`) captures all `audit` records per test and fails if any record violates the schema.
3. **CI** — The regular backend test job already exercises the plugin. A lightweight `audit-validation` job can be added if log-artifact post-processing is required.
4. **Prod** — A nightly GitHub Actions workflow (`audit-log-validate.yml`) downloads the last 24 h of CloudWatch logs, runs the same validator in _warn_ mode, and alerts on failures.

## 4 Redaction Rules

The schema intentionally excludes PII beyond `ip_address` and `user_agent`. Sensitive request data, tokens, passwords, or raw SQL must **never** be logged.

If additional context is required, include _opaque identifiers_ (order id, tx hash) rather than payloads.

## 5 SIEM Field Mapping (ELK/Splunk)

| JSON key    | Target field   | Notes                          |
| ----------- | -------------- | ------------------------------ |
| `timestamp` | `@timestamp`   | Parsed as UTC datetime         |
| `action`    | `event.action` |                                |
| `id`        | `event.id`     |                                |
| `trace_id`  | `trace.id`     | Correlates to application logs |
| `user_id`   | `user.id`      | (Auth events only)             |

A sample Logstash filter is provided under `ops/logstash/audit_filter.conf`.

---

© 2025 Trading-Bot SMC – Security & Compliance Team
