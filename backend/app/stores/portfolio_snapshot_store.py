from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.portfolio_snapshot_cache import PortfolioSnapshotCache


class PortfolioSnapshotStore:
    """
    Store layer for PortfolioSnapshot.
    Provides async CRUD and query methods for
    time-range and address-based retrieval.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_snapshot(
        self, snapshot: PortfolioSnapshot
    ) -> PortfolioSnapshot:
        """
        Persist a new PortfolioSnapshot to the database.
        """
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_snapshots_by_address_and_range(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PortfolioSnapshot]:
        """
        Retrieve all snapshots for a user address within a given
        timestamp range (inclusive), with pagination.
        """
        result = await self.db.execute(
            select(PortfolioSnapshot)
            .where(
                and_(
                    PortfolioSnapshot.user_address == user_address,
                    PortfolioSnapshot.timestamp >= from_ts,
                    PortfolioSnapshot.timestamp <= to_ts,
                )
            )
            .order_by(PortfolioSnapshot.timestamp)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_latest_snapshot_by_address(
        self, user_address: str
    ) -> Optional[PortfolioSnapshot]:
        """
        Retrieve the most recent snapshot for a user address.
        """
        result = await self.db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_address == user_address)
            .order_by(desc(PortfolioSnapshot.timestamp))
            .limit(1)
        )
        return result.scalars().first()

    async def delete_snapshot(self, snapshot_id: int) -> None:
        """
        Delete a PortfolioSnapshot by its ID.
        """
        snapshot = await self.db.get(PortfolioSnapshot, snapshot_id)
        if snapshot:
            await self.db.delete(snapshot)
            await self.db.commit()

    async def get_cache(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        interval: str,
        limit: int,
        offset: int,
    ) -> str | None:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(PortfolioSnapshotCache).where(
                PortfolioSnapshotCache.user_address == user_address,
                PortfolioSnapshotCache.from_ts == from_ts,
                PortfolioSnapshotCache.to_ts == to_ts,
                PortfolioSnapshotCache.interval == interval,
                PortfolioSnapshotCache.limit == limit,
                PortfolioSnapshotCache.offset == offset,
                (PortfolioSnapshotCache.expires_at is None)
                | (PortfolioSnapshotCache.expires_at > now),
            )
        )
        cache = result.scalars().first()
        return cache.response_json if cache else None

    async def set_cache(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        interval: str,
        limit: int,
        offset: int,
        response_json: str,
        expires_in_seconds: int = 3600,
    ):
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=expires_in_seconds)
        # Remove any existing cache for these params
        await self.db.execute(
            delete(PortfolioSnapshotCache).where(
                PortfolioSnapshotCache.user_address == user_address,
                PortfolioSnapshotCache.from_ts == from_ts,
                PortfolioSnapshotCache.to_ts == to_ts,
                PortfolioSnapshotCache.interval == interval,
                PortfolioSnapshotCache.limit == limit,
                PortfolioSnapshotCache.offset == offset,
            )
        )
        cache = PortfolioSnapshotCache(
            user_address=user_address,
            from_ts=from_ts,
            to_ts=to_ts,
            interval=interval,
            limit=limit,
            offset=offset,
            response_json=response_json,
            created_at=now,
            expires_at=expires_at,
        )
        self.db.add(cache)
        await self.db.commit()

    async def get_timeline(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        limit: int = 100,
        offset: int = 0,
        interval: str = "none",
    ) -> List[PortfolioSnapshot]:
        # Fetch all snapshots in range
        result = await self.db.execute(
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.user_address == user_address,
                PortfolioSnapshot.timestamp >= from_ts,
                PortfolioSnapshot.timestamp <= to_ts,
            )
            .order_by(PortfolioSnapshot.timestamp.asc())
        )
        snapshots = result.scalars().all()
        # Interval aggregation
        if interval == "none":
            filtered = snapshots
        elif interval == "daily":
            grouped = {}
            for snap in snapshots:
                day = datetime.utcfromtimestamp(snap.timestamp).date()
                if (
                    day not in grouped
                    or snap.timestamp > grouped[day].timestamp
                ):
                    grouped[day] = snap
            filtered = list(
                sorted(grouped.values(), key=lambda s: s.timestamp)
            )
        elif interval == "weekly":
            grouped = {}
            for snap in snapshots:
                dt = datetime.utcfromtimestamp(snap.timestamp)
                week = dt.isocalendar()[:2]  # (year, week)
                if (
                    week not in grouped
                    or snap.timestamp > grouped[week].timestamp
                ):
                    grouped[week] = snap
            filtered = list(
                sorted(grouped.values(), key=lambda s: s.timestamp)
            )
        else:
            raise ValueError("Invalid interval")
        # Pagination
        return filtered[offset : offset + limit]  # noqa: E203
