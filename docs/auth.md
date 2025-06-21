## JWKS Cache Invalidation & Operational Monitoring

### Overview
The JWKS endpoint (`/.well-known/jwks.json`) serves the current set of public keys for JWT verification. To ensure zero-downtime key rotation, the JWKS response is aggressively cached in Redis. However, whenever a key is promoted or retired, the cache must be invalidated immediately so clients always receive the latest keys.

### Integration Details
- **Trigger Point:** Cache invalidation is triggered by the JWT key rotation Celery task, specifically in the `_apply_key_set_update()` function.
- **Mechanism:** After key promotion/retirement, the task calls `invalidate_jwks_cache_sync()`, which deletes the JWKS cache key in Redis.
- **Error Handling:** If cache invalidation fails, the error is logged and an audit event is emitted, but the key rotation process continues. The cache will eventually expire based on its TTL (default: 1 hour).

### Audit Trail
- **Events Emitted:**
  - `JWKS_CACHE_INVALIDATED` (on success)
  - `JWKS_CACHE_INVALIDATION_FAILED` (on failure, with error details)
- **Fields:** Each event includes a timestamp, action, and context (e.g., reason, error message).

### Metrics & Monitoring
- **Prometheus Metrics:**
  - `jwt_jwks_cache_invalidations_total`: Number of successful cache invalidations
  - `jwt_jwks_cache_invalidation_errors_total`: Number of cache invalidation errors
- **Alerting:**
  - High error rates in cache invalidation should trigger operational alerts (e.g., via Slack webhook integration)
- **Logs:**
  - All cache invalidation attempts are logged at INFO level, with errors at WARNING level.

### Operational Best Practices
- **Monitor** the above metrics and audit events to ensure cache invalidation is working as expected.
- **Investigate** repeated cache invalidation failures promptly, as they may indicate Redis connectivity issues or misconfiguration.
- **Review** audit logs for `JWKS_CACHE_INVALIDATION_FAILED` events to diagnose root causes.

### Example Audit Log
```json
{"timestamp": "2025-06-22T12:34:56Z", "action": "JWKS_CACHE_INVALIDATED", "reason": "key_rotation"}
{"timestamp": "2025-06-22T12:35:01Z", "action": "JWKS_CACHE_INVALIDATION_FAILED", "error": "redis connection timeout"}
```

### Example Prometheus Metrics
```
jwt_jwks_cache_invalidations_total 42
jwt_jwks_cache_invalidation_errors_total 1
```

### Troubleshooting
- If clients are receiving stale keys after a rotation, check:
  - Redis availability and connectivity
  - Recent audit logs for cache invalidation failures
  - Prometheus metrics for error spikes
- If cache invalidation is failing but key rotation is succeeding, the system will eventually self-heal when the cache TTL expires, but operational visibility is critical for rapid remediation. 