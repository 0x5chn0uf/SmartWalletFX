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

## 3. Operational Checks & Troubleshooting

### Verifying Monitoring
- Ensure `/metrics` endpoint is reachable and metrics are updating.
- Check Prometheus server targets and scrape status.

### Verifying Alerting
- Confirm Slack alerts are received for test and real failures.
- Check backend logs for alerting errors or rate limiting warnings.

### Common Issues
- **No metrics exposed:**
  - Ensure `prometheus_client` is installed and enabled in config.
  - Check for import errors in logs.
- **No Slack alerts:**
  - Verify `SLACK_WEBHOOK_URL` and `SLACK_ALERTING_ENABLED` are set.
  - Check for rate limiting or network errors in logs.
- **Alert spam:**
  - Adjust `SLACK_MAX_ALERTS_PER_HOUR` as needed.

### Security
- Never log or expose webhook URLs or API keys.
- Store all secrets in environment variables or secure vaults.

---

## 4. References
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

_Last updated: 2025-06-22_ 