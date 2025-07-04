import json

from app.repositories.portfolio_snapshot_repository import (
    PortfolioSnapshotRepository,
)
from app.schemas.defi import PortfolioSnapshot as PortfolioSnapshotSchema


class PortfolioSnapshotUsecase:
    """
    Usecase for retrieving historical portfolio snapshots (timeline) for
    a user.
    """

    def __init__(self, repository: PortfolioSnapshotRepository):
        self.repository = repository

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
        cached = await self.repository.get_cache(
            user_address, from_ts, to_ts, interval, limit, offset
        )
        if cached:
            return [PortfolioSnapshotSchema(**obj) for obj in json.loads(cached)]
        # Compute result
        result = await self.repository.get_timeline(
            user_address, from_ts, to_ts, limit, offset, interval
        )
        # Convert to Pydantic models
        pydantic_result = [
            PortfolioSnapshotSchema.model_validate(r, from_attributes=True)
            for r in result
        ]

        # Cache the result as list of dicts
        await self.repository.set_cache(
            user_address=user_address,
            from_ts=from_ts,
            to_ts=to_ts,
            interval=interval,
            limit=limit,
            offset=offset,
            response_json=json.dumps([p.model_dump() for p in pydantic_result]),
        )
        return pydantic_result
