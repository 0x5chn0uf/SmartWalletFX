# Monitoring & Observability

This document outlines the monitoring and observability strategy for the SmartWalletFX platform, including metrics, logging, and alerting.

---

## 1. Overview

The platform implements comprehensive monitoring across multiple layers:

- **Application Metrics**: Prometheus metrics for performance and business logic
- **Audit Logging**: Structured JSON logs for security and compliance
- **Alerting**: Slack webhook integration for critical failures
- **Health Checks**: Endpoint monitoring for service availability

---

## 2. Prometheus Metrics

### 2.1 Database Backup Metrics

| Metric Name                  | Type      | Description                              | Labels |
| ---------------------------- | --------- | ---------------------------------------- | ------ |
| `db_backup_total`            | Counter   | Total number of backup attempts          | `env`  |
| `db_backup_failed_total`     | Counter   | Number of failed backup attempts         | `env`  |
| `db_backup_duration_seconds` | Histogram | Duration of backup operations in seconds | `env`  |
| `db_backup_size_bytes`       | Histogram | Size of backup files in bytes            | `env`  |

**Example Queries:**

```promql
# Backup success rate
(rate(db_backup_total[1h]) - rate(db_backup_failed_total[1h])) / rate(db_backup_total[1h]) * 100

# 95th percentile backup duration
histogram_quantile(0.95, rate(db_backup_duration_seconds_bucket[1h]))

# Average backup size
rate(db_backup_size_bytes_sum[1h]) / rate(db_backup_size_bytes_count[1h])
```

### 2.2 JWT Rotation Metrics (Task 112)

| Metric Name                         | Type      | Description                         | Labels             |
| ----------------------------------- | --------- | ----------------------------------- | ------------------ |
| `jwt_key_rotation_total`            | Counter   | Total key rotation attempts         | `env`, `operation` |
| `jwt_key_rotation_duration_seconds` | Histogram | Duration of key rotation operations | `env`              |
| `jwt_active_keys_total`             | Gauge     | Number of currently active JWT keys | `env`              |

### 2.3 Application Metrics

| Metric Name                     | Type      | Description                    | Labels                         |
| ------------------------------- | --------- | ------------------------------ | ------------------------------ |
| `http_requests_total`           | Counter   | Total HTTP requests            | `method`, `endpoint`, `status` |
| `http_request_duration_seconds` | Histogram | HTTP request duration          | `method`, `endpoint`           |
| `celery_task_total`             | Counter   | Total Celery task executions   | `task_name`, `status`          |
| `celery_task_duration_seconds`  | Histogram | Celery task execution duration | `task_name`                    |

---

## 3. Structured Logging

### 3.1 Log Categories

| Logger           | Purpose                      | Format                  |
| ---------------- | ---------------------------- | ----------------------- |
| `app`            | Application diagnostics      | JSON via structlog      |
| `audit`          | Security & compliance events | JSON (schema-validated) |
| `uvicorn.access` | HTTP access logs             | Plain text              |

### 3.2 Audit Event Types

**Authentication Events:**

- `user_login_success` / `user_login_failed`
- `token_refresh_success` / `token_refresh_failed`
- `jwt_key_rotated` / `jwt_key_rotation_failed`

**Database Events:**

- `db_backup_started` / `db_backup_succeeded` / `db_backup_failed`
- `db_restore_started` / `db_restore_succeeded` / `db_restore_failed`

**API Events:**

- `admin_endpoint_accessed`
- `sensitive_operation_performed`

### 3.3 Log Aggregation

**Local Development:**

```bash
# View audit logs
tail -f logs/audit.log | jq .

# Filter backup events
grep '"action":"db_backup"' logs/audit.log | jq .
```

**Production:**

- Logs are shipped to centralized logging (ELK/Loki)
- Audit logs are indexed for compliance queries
- Retention: 90 days for audit logs, 30 days for application logs

---

## 4. Alerting

### 4.1 Slack Integration

Critical failures trigger Slack alerts via webhook integration:

**Configuration:**

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

**Alert Types:**

- Database backup/restore failures
- JWT key rotation failures
- Application startup/shutdown events
- Critical error thresholds exceeded

**Alert Format:**

```
🚨 [ENVIRONMENT] Event Description
Error: detailed error message
Timestamp: 2025-06-22T14:30:00Z
```

### 4.2 Prometheus Alertmanager Rules

```yaml
groups:
  - name: backup.rules
    rules:
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
          summary: "Backup duration is high"
          description: "95th percentile backup duration is {{ $value }}s"

  - name: jwt.rules
    rules:
      - alert: JWTRotationFailure
        expr: increase(jwt_key_rotation_total{operation="failed"}[1h]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "JWT key rotation failed"
          description: "JWT key rotation has failed {{ $value }} times in the last hour"
```

---

## 5. Health Checks

### 5.1 Application Health

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-06-22T14:30:00Z",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  }
}
```

### 5.2 Monitoring Health Checks

**Database Connectivity:**

```promql
up{job="postgres"} == 1
```

**Redis Connectivity:**

```promql
redis_up == 1
```

**Celery Workers:**

```promql
celery_workers_active > 0
```

---

## 6. Dashboards

### 6.1 Grafana Dashboard Recommendations

**System Overview Dashboard:**

- Application uptime and response times
- Database connection pool status
- Celery queue lengths and worker status
- Error rate trends

**Backup Operations Dashboard:**

- Backup success rate over time
- Backup duration trends
- Backup size growth
- Failed backup alerts
- Storage utilization

**Security Dashboard:**

- Authentication success/failure rates
- JWT key rotation status
- Audit event frequency
- Suspicious activity patterns

### 6.2 Key Performance Indicators (KPIs)

| Metric                              | Target  | Critical Threshold |
| ----------------------------------- | ------- | ------------------ |
| Application Uptime                  | 99.9%   | < 99.5%            |
| API Response Time (95th percentile) | < 200ms | > 500ms            |
| Backup Success Rate                 | 100%    | < 95%              |
| Error Rate                          | < 0.1%  | > 1%               |
| JWT Key Rotation Success            | 100%    | < 100%             |

---

## 7. Troubleshooting

### 7.1 Common Issues

**High Backup Duration:**

1. Check database size growth: `histogram_quantile(0.95, rate(db_backup_size_bytes_bucket[24h]))`
2. Verify disk I/O performance
3. Consider compression settings

**Backup Failures:**

1. Check audit logs: `grep '"action":"db_backup_failed"' /var/log/audit.log`
2. Verify database connectivity
3. Check disk space availability
4. Review PostgreSQL logs

**Missing Metrics:**

1. Verify Prometheus scraping configuration
2. Check application `/metrics` endpoint
3. Ensure metrics are properly labeled

### 7.2 Log Analysis

**Find Recent Backup Operations:**

```bash
# Last 24 hours of backup events
grep '"action":"db_backup"' /var/log/audit.log | \
  jq 'select(.timestamp > (now - 86400 | todate))'
```

**Analyze Backup Performance:**

```bash
# Extract backup durations from audit logs
grep '"action":"db_backup_succeeded"' /var/log/audit.log | \
  jq -r '.size_bytes' | \
  awk '{sum+=$1; count++} END {print "Average size:", sum/count, "bytes"}'
```

---

## 8. Maintenance

### 8.1 Regular Tasks

**Weekly:**

- Review dashboard for anomalies
- Check alert rule effectiveness
- Verify log retention policies

**Monthly:**

- Update monitoring thresholds based on trends
- Review and rotate monitoring credentials
- Audit monitoring coverage for new features

**Quarterly:**

- Capacity planning based on growth trends
- Monitoring tool updates and security patches
- Review and update alerting escalation procedures

### 8.2 Monitoring the Monitors

**Prometheus Self-Monitoring:**

```promql
# Prometheus targets down
up == 0

# High cardinality metrics
prometheus_tsdb_
_series > 1000000
```

**Alertmanager Health:**

```promql
# Alertmanager instances down
up{job="alertmanager"} == 0

# Undelivered alerts
alertmanager_notifications_failed_total > 0
```

---

## © 2025 SmartWalletFX – Infrastructure & DevOps Team

# Monitoring & Alerting – JWT Key Rotation

## Overview

This document describes how to configure, operate, and verify monitoring and alerting for the automated JWT key rotation system. It covers Prometheus metrics setup, Slack alerting configuration, operational checks, and troubleshooting.

---

## 1. Prometheus Metrics Setup

### Enabling Metrics

- The backend exposes Prometheus metrics for JWT key rotation, including:
  - `jwt_key_rotations_total`: Number of times a new JWT signing key has been promoted.
  - `jwt_key_retirements_total`: Number of JWT signing keys retired.
  - `jwt_key_rotation_errors_total`: Number of errors encountered during key rotation.
- Metrics are collected using the `prometheus_client` library (specified in `pyproject.toml`).
- Centralized Prometheus setup is in `app/monitoring/prometheus.py`.

### Metrics Endpoint

- By default, metrics can be exposed via a FastAPI route or a dedicated HTTP server.
- **Recommended:** Add a `/metrics` endpoint to your FastAPI app:

```python
from fastapi import APIRouter, Response
from app.monitoring.prometheus import generate_metrics

router = APIRouter()

@router.get("/metrics")
def metrics():
    data, content_type = generate_metrics()
    return Response(content=data, media_type=content_type)
```

- Or, start a standalone metrics server:

```python
from app.monitoring.prometheus import start_metrics_server
start_metrics_server(port=9090, addr="0.0.0.0")
```

### Configuration

- Metrics settings are in `core/config.py`:
  - `PROMETHEUS_ENABLED`: Enable/disable metrics (default: True)
  - `PROMETHEUS_PORT`, `PROMETHEUS_HOST`: Server binding

### Verification

- Visit `http://localhost:9090/metrics` (or your configured endpoint) to verify metrics are exposed.
- Use `curl` or Prometheus server to scrape metrics.

---

## 2. Slack Alerting Setup

### Enabling Alerting

- Slack alerting is implemented in `app/utils/alerting.py`.
- Alerts are sent on JWT rotation failures, with severity and rate limiting.

### Configuration

- Set the following environment variables or update `.env`:
  - `SLACK_WEBHOOK_URL`: Slack webhook URL for alerts
  - `SLACK_ALERTING_ENABLED`: Set to `true` to enable alerting
  - `SLACK_MAX_ALERTS_PER_HOUR`: Rate limit (default: 10)
  - `SLACK_TIMEOUT_SECONDS`: HTTP timeout (default: 10)
  - `JWT_ROTATION_ALERT_ON_ERROR`: Set to `true` to alert on errors
  - `JWT_ROTATION_ALERT_ON_RETRY`: Set to `true` to alert on retries

### Operational Playbook

- On rotation failure, an alert is sent to the configured Slack channel.
- Alerts include severity, error message, and context fields.
- Rate limiting prevents alert spam.

### Verification

- Trigger a test alert (e.g., by forcing a rotation error) and confirm receipt in Slack.
- Check logs for `Slack alert sent successfully` or error messages.

---

## 3. JWT Key Rotation Specific Monitoring

### Key Rotation Metrics

The JWT key rotation system exposes specific metrics that should be monitored:

```bash
# Check rotation activity
curl -s http://localhost:9090/metrics | grep jwt_key_rotations_total

# Monitor retirements
curl -s http://localhost:9090/metrics | grep jwt_key_retirements_total

# Watch for errors
curl -s http://localhost:9090/metrics | grep jwt_key_rotation_errors_total
```

### Expected Behavior

- **Normal Operation**: `jwt_key_rotations_total` should increment periodically (every 5 minutes by default)
- **Key Lifecycle**: `jwt_key_retirements_total` should increment when keys are retired
- **Error-Free**: `jwt_key_rotation_errors_total` should remain at 0 or very low

### Alerting Thresholds

Configure alerts for the following conditions:

- **No rotation activity**: `jwt_key_rotations_total` hasn't increased in 15 minutes
- **High error rate**: `jwt_key_rotation_errors_total` > 5 in 1 hour
- **Lock contention**: Multiple rotation attempts failing due to Redis lock

### Grafana Dashboard

Create a dashboard with the following panels:

1. **Rotation Activity**: Line chart of `jwt_key_rotations_total` over time
2. **Retirement Activity**: Line chart of `jwt_key_retirements_total` over time
3. **Error Rate**: Line chart of `jwt_key_rotation_errors_total` over time
4. **Current Key Status**: Gauge showing active key age and next rotation time

---

## 4. Operational Checks & Troubleshooting

### Verifying Monitoring

- Ensure `/metrics` endpoint is reachable and metrics are updating.
- Check Prometheus server targets and scrape status.

### Verifying Alerting

- Confirm Slack alerts are received for test and real failures.
- Check backend logs for alerting errors or rate limiting warnings.

### JWT Rotation Specific Checks

- **Celery Beat Scheduler**: Verify the rotation task is scheduled correctly
- **Redis Lock**: Check that the distributed lock is working properly
- **Key Configuration**: Ensure `JWT_KEYS` and `ACTIVE_JWT_KID` are properly set
- **Grace Period**: Verify grace period settings align with token TTL

### Common Issues

- **No metrics exposed:**
  - Ensure `prometheus_client` is installed and enabled in config.
  - Check for import errors in logs.
- **No Slack alerts:**
  - Verify `SLACK_WEBHOOK_URL` and `SLACK_ALERTING_ENABLED` are set.
  - Check for rate limiting or network errors in logs.
- **Alert spam:**
  - Adjust `SLACK_MAX_ALERTS_PER_HOUR` as needed.
- **No rotation activity:**
  - Check Celery beat scheduler is running
  - Verify Redis connectivity for distributed locking
  - Confirm key configuration is valid

### Security

- Never log or expose webhook URLs or API keys.
- Store all secrets in environment variables or secure vaults.

---

## 5. Integration with Existing Monitoring

### Prometheus Integration

- The JWT rotation metrics integrate seamlessly with existing Prometheus infrastructure
- Use existing alerting rules and notification channels
- Leverage existing Grafana dashboards and visualization

### Log Aggregation

- JWT rotation audit events are structured JSON logs
- Integrate with existing log aggregation systems (ELK, Splunk, etc.)
- Use correlation IDs to trace rotation activities across systems

### Incident Response

- JWT rotation failures should trigger existing incident response procedures
- Integrate with existing on-call schedules and escalation policies
- Use existing communication channels for incident coordination

---

## 6. References

- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [JWT Key Rotation Playbook](auth_key_rotation.md) - Complete operational guide

---

_Last updated: 2025-06-22_
