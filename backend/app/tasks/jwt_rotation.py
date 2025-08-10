"""Celery task orchestrating automated JWT key promotion/retirement.

This module is *impure* by design – it coordinates I/O (Redis locking, metrics,
audit logs, mutation of ``app.core.config.settings``) around the *pure* state
machine implemented in :pymod:`app.utils.jwt_rotation`.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.celery_app import celery
from app.core.config import Configuration
from app.utils.jwt_rotation import (
    Key,
    KeySet,
    KeySetUpdate,
    promote_and_retire_keys,
)
from app.utils.logging import Audit
from app.utils.redis_lock import acquire_lock

# Shared configuration instance for state consistency
_config = Configuration()

# ---------------------------------------------------------------------------
# Prometheus metrics – gracefully degrade to no-op counters if the optional
# dependency is not installed.
# ---------------------------------------------------------------------------

try:
    from prometheus_client import Counter  # type: ignore

    _PROMOTE_C = Counter(
        "jwt_key_rotations_total",
        "Number of times a new JWT signing key has been promoted to active.",
    )
    _RETIRE_C = Counter(
        "jwt_key_retirements_total",
        "Number of JWT signing keys retired by the automated scheduler.",
    )
    _ERROR_C = Counter(
        "jwt_key_rotation_errors_total",
        "Number of errors encountered during automated key rotation.",
    )
    _CACHE_INVALIDATION_C = Counter(
        "jwt_jwks_cache_invalidations_total",
        "Number of times the JWKS cache has been invalidated during key rotation.",
    )
    _CACHE_INVALIDATION_ERROR_C = Counter(
        "jwt_jwks_cache_invalidation_errors_total",
        "Number of errors encountered during JWKS cache invalidation.",
    )

    class _MetricsWrapper:
        def __init__(self, c):
            self._c = c

        def inc(self, n: int = 1) -> None:  # noqa: D401 – simple pass-through
            self._c.inc(n)

    METRICS = {
        "promote": _MetricsWrapper(_PROMOTE_C),
        "retire": _MetricsWrapper(_RETIRE_C),
        "error": _MetricsWrapper(_ERROR_C),
        "cache_invalidation": _MetricsWrapper(_CACHE_INVALIDATION_C),
        "cache_invalidation_error": _MetricsWrapper(_CACHE_INVALIDATION_ERROR_C),
    }

except ImportError:  # pragma: no cover – prometheus_client optional dependency

    class _NoOpMetric:  # noqa: D401 – minimal stub
        def inc(self, _n: int = 1) -> None:  # noqa: D401 – no-op
            return

    METRICS = {
        k: _NoOpMetric()
        for k in (
            "promote",
            "retire",
            "error",
            "cache_invalidation",
            "cache_invalidation_error",
        )
    }


def _gather_current_key_set() -> KeySet:
    """Build a :class:`KeySet` instance from *settings* and runtime state."""

    from app.utils import jwt as jwt_utils  # local import to avoid cycles

    keys: dict[str, Key] = {}

    # 1. In-memory map from settings
    for kid, val in _config.JWT_KEYS.items():
        retired_at = jwt_utils._RETIRED_KEYS.get(
            kid
        )  # pylint: disable=protected-access
        keys[kid] = Key(kid=kid, value=val, retired_at=retired_at)

    # 2. Derive *next_kid* naively: first non-active key in insertion order.
    next_kid: Optional[str] = None
    for kid in keys:
        if kid != _config.ACTIVE_JWT_KID:
            next_kid = kid
            break

    return KeySet(
        keys=keys,
        active_kid=_config.ACTIVE_JWT_KID,
        next_kid=next_kid,
        grace_period_seconds=_config.JWT_ROTATION_GRACE_PERIOD_SECONDS,
    )


def _apply_key_set_update(update: KeySetUpdate) -> None:
    """Mutate *settings* and runtime state to reflect *update* decisions."""

    if update.is_noop():
        return

    from app.utils import jwt as jwt_utils  # local import to avoid cycles

    # Import inside function so monkey-patching in tests is respected;
    # importing at call time picks up patched object.
    from app.utils.jwks_cache import JWKSCacheUtils

    now = datetime.now(timezone.utc)

    # Promote new active key
    if update.new_active_kid:
        old_kid = _config.ACTIVE_JWT_KID
        _config.ACTIVE_JWT_KID = update.new_active_kid
        Audit.info("JWT key promoted", new_kid=update.new_active_kid, old_kid=old_kid)
        METRICS["promote"].inc()

    # Retire keys
    for kid in update.keys_to_retire:
        # Mark key as retired so verification rejects it after grace period.
        jwt_utils._RETIRED_KEYS[kid] = now  # pylint: disable=protected-access
        Audit.info("JWT key retired", kid=kid)
        METRICS["retire"].inc()

    # Invalidate JWKS cache to ensure fresh keys are published immediately
    # This is fire-and-forget - failures don't break the rotation process
    try:
        jwks_cache_utils = JWKSCacheUtils(_config)
        success = jwks_cache_utils.invalidate_jwks_cache_sync()
        if success:
            Audit.info("JWKS cache invalidated", reason="key_rotation")
            METRICS["cache_invalidation"].inc()
        else:
            Audit.warning(
                "JWKS cache invalidation failed",
                error="cache_invalidation_returned_false",
            )
            METRICS["cache_invalidation_error"].inc()
    except Exception as e:
        Audit.warning(
            "Failed to invalidate JWKS cache during key rotation", error=str(e)
        )
        METRICS["cache_invalidation_error"].inc()


def _build_redis_client():  # pragma: no cover – isolation for patching
    """Return an *async* Redis client instance configured from environment."""

    from redis.asyncio import (
        Redis,  # imported lazily to avoid heavy dep at import
    )

    redis_url = _config.REDIS_URL or "redis://localhost:6379/0"
    return Redis.from_url(redis_url)


# ---------------------------------------------------------------------------
# Celery task entry-point
# ---------------------------------------------------------------------------


@celery.task(bind=True, name="app.tasks.jwt_rotation.promote_and_retire_keys_task")
def promote_and_retire_keys_task(self):  # noqa: D401 – Celery signature
    """Automated promotion & retirement of JWT signing keys.

    1. Acquire a Redis-based distributed lock to ensure single-worker execution.
    2. Load the current key-set state.
    3. Run the *pure* decision function to determine required changes.
    4. Apply changes (promotion / retirement) and emit audit logs + metrics.
    5. Retry with exponential back-off on transient failures.
    """

    async def _run() -> None:  # noqa: D401 – nested coroutine
        redis = _build_redis_client()
        try:
            async with acquire_lock(
                redis,
                "jwt_key_rotation",
                timeout=_config.JWT_ROTATION_LOCK_TTL_SEC,
            ) as got_lock:
                if not got_lock:
                    Audit.debug("JWT key rotation: lock not acquired – skipping run.")
                    return

                key_set = _gather_current_key_set()
                update = promote_and_retire_keys(key_set, datetime.now(timezone.utc))

                if update.is_noop():
                    Audit.debug("JWT key rotation: no changes needed.")
                    return

                _apply_key_set_update(update)
        finally:
            await redis.close()

    try:
        asyncio.run(_run())
    except Exception as exc:  # pragma: no cover – capture unexpected errors
        Audit.error("JWT key rotation failed", error=str(exc))
        METRICS["error"].inc()
        # Exponential back-off: double countdown each retry up to 1h.
        retry_delay = min(60 * 60, (self.request.retries + 1) * 60)  # 1m,2m,...,60m
        raise self.retry(exc=exc, countdown=retry_delay)
