"""Domain services implementing business rules for DeFi aggregation."""

from __future__ import annotations

import asyncio
from typing import Sequence

from .models import AggregateMetrics, Position
from .repositories import AggregateMetricsRepository


class ProtocolAdapter(  # pragma: no cover – runtime implementation lives in infra layer
    # pylint: disable=too-few-public-methods
):
    """Simple protocol adapter interface (hexagonal *secondary port*)."""

    async def fetch_positions(self, wallet_id: str) -> Sequence[Position]:  # noqa: D401
        """Return positions for the given wallet."""
        raise NotImplementedError


class AggregatorService:
    """Aggregate metrics from multiple protocol adapters."""

    def __init__(
        self,
        adapters: Sequence[ProtocolAdapter],
        repository: AggregateMetricsRepository,
    ) -> None:
        self._adapters = adapters
        self._repository = repository

    async def aggregate(self, wallet_id: str) -> AggregateMetrics:
        """Compute aggregate metrics and persist them."""
        # Fetch positions concurrently
        positions_lists = await asyncio.gather(
            *[adapter.fetch_positions(wallet_id) for adapter in self._adapters],
            return_exceptions=False,
        )
        positions: list[Position] = [p for sub in positions_lists for p in sub]

        # Positive amounts are supplies/stakes, negatives are borrowings
        tvl = sum(p.usd_value for p in positions if p.amount >= 0)
        total_borrowings = sum(abs(p.usd_value) for p in positions if p.amount < 0)

        weighted_sum = sum(
            p.usd_value * p.apy
            for p in positions
            if p.apy is not None and p.amount >= 0
        )
        aggregate_apy = (weighted_sum / tvl) if tvl and weighted_sum else None

        metrics = AggregateMetrics.new(wallet_id=wallet_id)
        metrics.tvl = tvl
        metrics.total_borrowings = total_borrowings
        metrics.aggregate_apy = aggregate_apy
        metrics.positions = positions

        # Persist (fire-and-forget – don't block API response)
        await self._repository.upsert(metrics)
        return metrics
