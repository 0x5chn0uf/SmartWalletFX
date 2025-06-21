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
- Metrics are collected using the `prometheus_client` library (required in `requirements/base.txt`).
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