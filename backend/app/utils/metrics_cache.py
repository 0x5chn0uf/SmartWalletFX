"""Redis caching utilities for DeFi aggregate metrics.

This mirrors the JWKS caching helper but is parameterised by *wallet_id* so
multiple keys can coexist.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from redis.asyncio import Redis

from app.domain.defi_tracker.schemas import AggregateMetricsSchema

logger = logging.getLogger(__name__)

CACHE_PREFIX = "defi:agg:"
DEFAULT_TTL_SEC = 60  # 1 minute – refreshed frequently by aggregator


async def get_metrics_cache(
    redis: Redis, wallet_id: str
) -> Optional[AggregateMetricsSchema]:
    """Retrieve cached :class:`AggregateMetricsSchema` for *wallet_id*."""
    key = f"{CACHE_PREFIX}{wallet_id.lower()}"
    try:
        raw = await redis.get(key)
        if raw:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            data = json.loads(raw)
            return AggregateMetricsSchema(**data)
    except Exception as exc:  # noqa: BLE001 – log only
        logger.warning("Failed to read aggregate metrics cache: %s", exc)
    return None


async def set_metrics_cache(
    redis: Redis,
    wallet_id: str,
    metrics: AggregateMetricsSchema,
    ttl: int = DEFAULT_TTL_SEC,
) -> bool:
    """Store *metrics* in Redis for *wallet_id* with **ttl** seconds."""
    key = f"{CACHE_PREFIX}{wallet_id.lower()}"
    try:
        await redis.setex(key, ttl, metrics.model_dump_json())
        return True
    except Exception as exc:  # noqa: BLE001 – log only
        logger.warning("Failed to store aggregate metrics cache: %s", exc)
        return False
