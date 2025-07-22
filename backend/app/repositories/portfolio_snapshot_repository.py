from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, delete, desc, or_, select

from app.core.database import CoreDatabase
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.portfolio_snapshot_cache import PortfolioSnapshotCache
from app.utils.logging import Audit


class PortfolioSnapshotRepository:
    """Repository for :class:`~app.models.portfolio_snapshot.PortfolioSnapshot`."""

    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    async def create_snapshot(self, snapshot: PortfolioSnapshot) -> PortfolioSnapshot:
        """Persist a new snapshot and return it back refreshed."""
        self.__audit.info(
            "portfolio_snapshot_repository_create_snapshot_started",
            user_address=snapshot.user_address,
            timestamp=snapshot.timestamp,
        )

        try:
            async with self.__database.get_session() as session:
                session.add(snapshot)
                await session.commit()
                await session.refresh(snapshot)

                self.__audit.info(
                    "portfolio_snapshot_repository_create_snapshot_success",
                    user_address=snapshot.user_address,
                    timestamp=snapshot.timestamp,
                    snapshot_id=snapshot.id,
                )
                return snapshot
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_repository_create_snapshot_failed",
                user_address=snapshot.user_address,
                timestamp=snapshot.timestamp,
                error=str(e),
            )
            raise

    async def get_snapshots_by_address_and_range(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PortfolioSnapshot]:
        """Get snapshots by address and timestamp range."""
        self.__audit.info(
            "portfolio_snapshot_repository_get_by_range_started",
            user_address=user_address,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=limit,
            offset=offset,
        )

        try:
            async with self.__database.get_session() as session:
                result = await session.execute(
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
                snapshots = result.scalars().all()

                self.__audit.info(
                    "portfolio_snapshot_repository_get_by_range_success",
                    user_address=user_address,
                    from_ts=from_ts,
                    to_ts=to_ts,
                    count=len(snapshots),
                )
                return snapshots
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_repository_get_by_range_failed",
                user_address=user_address,
                from_ts=from_ts,
                to_ts=to_ts,
                error=str(e),
            )
            raise

    async def get_latest_snapshot_by_address(
        self, user_address: str
    ) -> Optional[PortfolioSnapshot]:
        """Get the latest snapshot for a given address."""
        self.__audit.info(
            "portfolio_snapshot_repository_get_latest_started",
            user_address=user_address,
        )

        try:
            async with self.__database.get_session() as session:
                result = await session.execute(
                    select(PortfolioSnapshot)
                    .where(PortfolioSnapshot.user_address == user_address)
                    .order_by(desc(PortfolioSnapshot.timestamp))
                    .limit(1)
                )
                snapshot = result.scalars().first()

                self.__audit.info(
                    "portfolio_snapshot_repository_get_latest_success",
                    user_address=user_address,
                    found=snapshot is not None,
                )
                return snapshot
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_repository_get_latest_failed",
                user_address=user_address,
                error=str(e),
            )
            raise

    async def get_by_wallet_address(
        self, wallet_address: str
    ) -> List[PortfolioSnapshot]:
        """Get portfolio snapshots for a specific wallet address."""
        self.__audit.info(
            "portfolio_snapshot_repository_get_by_wallet_address_started",
            wallet_address=wallet_address,
        )

        try:
            async with self.__database.get_session() as session:
                result = await session.execute(
                    select(PortfolioSnapshot)
                    .where(PortfolioSnapshot.user_address == wallet_address)
                    .order_by(desc(PortfolioSnapshot.timestamp))
                )
                snapshots = result.scalars().all()

                self.__audit.info(
                    "portfolio_snapshot_repository_get_by_wallet_address_success",
                    wallet_address=wallet_address,
                    count=len(snapshots),
                )
                return snapshots
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_repository_get_by_wallet_address_failed",
                wallet_address=wallet_address,
                error=str(e),
            )
            raise

    async def delete_snapshot(self, snapshot_id: int) -> None:
        """Delete a snapshot by ID."""
        self.__audit.info(
            "portfolio_snapshot_repository_delete_started", snapshot_id=snapshot_id
        )

        try:
            async with self.__database.get_session() as session:
                snapshot = await session.get(PortfolioSnapshot, snapshot_id)
                if snapshot:
                    await session.delete(snapshot)
                    await session.commit()

                    self.__audit.info(
                        "portfolio_snapshot_repository_delete_success",
                        snapshot_id=snapshot_id,
                        found=snapshot is not None,
                    )
                else:
                    self.__audit.warning(
                        "portfolio_snapshot_repository_delete_not_found",
                        snapshot_id=snapshot_id,
                    )
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_repository_delete_failed",
                snapshot_id=snapshot_id,
                error=str(e),
            )
            raise

    # ------------------------------------------------------------------
    # Caching helpers
    # ------------------------------------------------------------------

    async def get_cache(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        interval: str,
        limit: int,
        offset: int,
    ) -> str | None:
        """Get cached response for given parameters."""
        self.__audit.info(
            "portfolio_snapshot_repository_get_cache_started",
            user_address=user_address,
            from_ts=from_ts,
            to_ts=to_ts,
            interval=interval,
        )

        try:
            async with self.__database.get_session() as session:
                now = datetime.utcnow()
                result = await session.execute(
                    select(PortfolioSnapshotCache).where(
                        PortfolioSnapshotCache.user_address == user_address,
                        PortfolioSnapshotCache.from_ts == from_ts,
                        PortfolioSnapshotCache.to_ts == to_ts,
                        PortfolioSnapshotCache.interval == interval,
                        PortfolioSnapshotCache.limit == limit,
                        PortfolioSnapshotCache.offset == offset,
                        or_(
                            PortfolioSnapshotCache.expires_at is None,
                            PortfolioSnapshotCache.expires_at > now,
                        ),
                    )
                )
                cache = result.scalars().first()

                self.__audit.info(
                    "portfolio_snapshot_repository_get_cache_success",
                    user_address=user_address,
                    found=cache is not None,
                )
                return cache.response_json if cache else None
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_repository_get_cache_failed",
                user_address=user_address,
                error=str(e),
            )
            raise

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
        """Set cached response for given parameters."""
        self.__audit.info(
            "portfolio_snapshot_repository_set_cache_started",
            user_address=user_address,
            from_ts=from_ts,
            to_ts=to_ts,
            interval=interval,
            expires_in_seconds=expires_in_seconds,
        )

        try:
            async with self.__database.get_session() as session:
                now = datetime.utcnow()
                expires_at = now + timedelta(seconds=expires_in_seconds)

                # Delete existing cache entries
                await session.execute(
                    delete(PortfolioSnapshotCache).where(
                        PortfolioSnapshotCache.user_address == user_address,
                        PortfolioSnapshotCache.from_ts == from_ts,
                        PortfolioSnapshotCache.to_ts == to_ts,
                        PortfolioSnapshotCache.interval == interval,
                        PortfolioSnapshotCache.limit == limit,
                        PortfolioSnapshotCache.offset == offset,
                    )
                )

                # Create new cache entry
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
                session.add(cache)
                await session.commit()

                self.__audit.info(
                    "portfolio_snapshot_repository_set_cache_success",
                    user_address=user_address,
                    from_ts=from_ts,
                    to_ts=to_ts,
                    interval=interval,
                )
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_repository_set_cache_failed",
                user_address=user_address,
                error=str(e),
            )
            raise

    # ------------------------------------------------------------------
    # Domain-specific helpers
    # ------------------------------------------------------------------

    async def get_timeline(
        self,
        user_address: str,
        from_ts: int,
        to_ts: int,
        limit: int = 100,
        offset: int = 0,
        interval: str = "none",
    ) -> List[PortfolioSnapshot]:
        """Get timeline of snapshots with optional interval grouping."""
        self.__audit.info(
            "portfolio_snapshot_repository_get_timeline_started",
            user_address=user_address,
            from_ts=from_ts,
            to_ts=to_ts,
            interval=interval,
            limit=limit,
            offset=offset,
        )

        try:
            async with self.__database.get_session() as session:
                result = await session.execute(
                    select(PortfolioSnapshot)
                    .where(
                        PortfolioSnapshot.user_address == user_address,
                        PortfolioSnapshot.timestamp >= from_ts,
                        PortfolioSnapshot.timestamp <= to_ts,
                    )
                    .order_by(PortfolioSnapshot.timestamp.asc())
                )
                snapshots = result.scalars().all()

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
                    filtered = sorted(grouped.values(), key=lambda snap: snap.timestamp)
                elif interval == "weekly":
                    grouped = {}
                    for snap in snapshots:
                        dt = datetime.utcfromtimestamp(snap.timestamp)
                        week = dt.isocalendar()[:2]
                        if (
                            week not in grouped
                            or snap.timestamp > grouped[week].timestamp
                        ):
                            grouped[week] = snap
                    filtered = sorted(grouped.values(), key=lambda snap: snap.timestamp)
                else:
                    raise ValueError("Invalid interval")

                # Slice pagination (ignore E203 whitespace rule for flake8/black)
                result_snapshots = filtered[offset : offset + limit]  # noqa: E203

                self.__audit.info(
                    "portfolio_snapshot_repository_get_timeline_success",
                    user_address=user_address,
                    interval=interval,
                    total_count=len(snapshots),
                    filtered_count=len(filtered),
                    result_count=len(result_snapshots),
                )
                return result_snapshots
        except Exception as e:
            self.__audit.error(
                "portfolio_snapshot_repository_get_timeline_failed",
                user_address=user_address,
                interval=interval,
                error=str(e),
            )
            raise
