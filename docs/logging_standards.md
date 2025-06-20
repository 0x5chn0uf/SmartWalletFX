# Logging Standards & Audit Events

This document defines the project-wide conventions for **structured JSON logging** and, in particular, the *audit* event format enforced by Subtask 4.16.

## 1  Log Categories

| Logger name | Purpose | Format |
|-------------|---------|--------|
| `uvicorn.access` | HTTP access logs emitted by the ASGI server | Plain-text (left as default; parsed by Ingest pipeline) |
| `app` (root) | Application diagnostic logs | JSON via `structlog` |
| `audit` | *Security-grade* events required for compliance / SIEM | JSON – **MUST** conform to the schemas in `app.schemas.audit_log` |

## 2  Audit Event Schema (v1)

Every audit record **MUST** include the following canonical fields; additional keys are allowed and schema-validated under `extra="allow"`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` (uuid4-hex) | Unique identifier for the log line (correlates multi-line events) |
| `timestamp` | ISO-8601 UTC | Event creation time |
| `action` | `str` | Machine-readable event name, e.g. `user_login_success` |
| `trace_id` | `str | null` | Request correlation id (propagated via middleware) |

Concrete subclasses add their own required keys, e.g. `AuthEvent.result`, `DBEvent.sha256` etc.

The authoritative schema lives in `backend/app/schemas/audit_log.py`.  A machine-readable JSON Schema representation is exportable via:

```python
from app.schemas.audit_log import audit_json_schema
print(audit_json_schema())
```

## 3  Validation Pipeline

1. **Runtime** — Every call to `app.utils.logging.audit()` injects mandatory keys and *then* passes the payload to `validate_audit_event()`. Behaviour is tuned via `AUDIT_VALIDATION` env-var:
   • `hard` (default in tests) → raise on validation failure  
   • `warn` → emit `warnings.warn` but continue  
   • `off`  → skip validation (perf mode)
2. **Tests** — A pytest plugin (`tests.plugins.audit_validator`) captures all `audit` records per test and fails if any record violates the schema.
3. **CI** — The regular backend test job already exercises the plugin. A lightweight `audit-validation` job can be added if log-artifact post-processing is required.
4. **Prod** — A nightly GitHub Actions workflow (`audit-log-validate.yml`) downloads the last 24 h of CloudWatch logs, runs the same validator in *warn* mode, and alerts on failures.

## 4  Redaction Rules

The schema intentionally excludes PII beyond `ip_address` and `user_agent`.  Sensitive request data, tokens, passwords, or raw SQL must **never** be logged.

If additional context is required, include *opaque identifiers* (order id, tx hash) rather than payloads.

## 5  SIEM Field Mapping (ELK/Splunk)

| JSON key | Target field | Notes |
|----------|--------------|-------|
| `timestamp` | `@timestamp` | Parsed as UTC datetime |
| `action` | `event.action` | | 
| `id` | `event.id` | |
| `trace_id` | `trace.id` | Correlates to application logs |
| `user_id` | `user.id` | (Auth events only) |

A sample Logstash filter is provided under `ops/logstash/audit_filter.conf`.

---
© 2025 Trading-Bot SMC – Security & Compliance Team 