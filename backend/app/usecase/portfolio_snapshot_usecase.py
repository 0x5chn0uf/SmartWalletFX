import json

from app.schemas.defi import PortfolioSnapshot as PortfolioSnapshotSchema
from app.stores.portfolio_snapshot_store import PortfolioSnapshotStore


def sa_obj_to_dict(obj):
    # Convert SQLAlchemy model instance to dict,
    # excluding private and relationship attributes
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


class PortfolioSnapshotUsecase:
    """
    Usecase for retrieving historical portfolio snapshots (timeline) for
    a user.
    """

    def __init__(self, store: PortfolioSnapshotStore):
        self.store = store

    async def get_timeline(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        limit: int = 100,
        offset: int = 0,
        interval: str = "none",
    ) -> list[PortfolioSnapshotSchema]:
        """
        Fetch portfolio snapshots for a user address within a
        given timestamp range, with pagination and interval aggregation.
        Uses database cache for performance.
        """
        # Try cache
        cached = await self.store.get_cache(
            user_address, from_ts, to_ts, interval, limit, offset
        )
        if cached:
            return [
                PortfolioSnapshotSchema(**obj) for obj in json.loads(cached)
            ]
        # Compute result
        result = await self.store.get_timeline(
            user_address, from_ts, to_ts, limit, offset, interval
        )
        # Convert to Pydantic models
        pydantic_result = [
            PortfolioSnapshotSchema(
                user_address=r.user_address,
                timestamp=r.timestamp,
                total_collateral=r.total_collateral,
                total_borrowings=r.total_borrowings,
                total_collateral_usd=r.total_collateral_usd,
                total_borrowings_usd=r.total_borrowings_usd,
                aggregate_health_score=r.aggregate_health_score,
                aggregate_apy=r.aggregate_apy,
                collaterals=r.collaterals,
                borrowings=r.borrowings,
                staked_positions=r.staked_positions,
                health_scores=r.health_scores,
                protocol_breakdown=r.protocol_breakdown,
            )
            for r in result
        ]
        # Cache the result as list of dicts
        await self.store.set_cache(
            user_address=user_address,
            from_ts=from_ts,
            to_ts=to_ts,
            interval=interval,
            limit=limit,
            offset=offset,
            response_json=json.dumps(
                [p.model_dump() for p in pydantic_result]
            ),
        )
        return pydantic_result
