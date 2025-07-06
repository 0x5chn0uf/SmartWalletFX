"""AuditLog repository implementing basic CRUD operations."""

from __future__ import annotations

import uuid
from typing import Any, Optional, Sequence

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Repository providing data-access helpers for :class:`AuditLog`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **data: Any) -> AuditLog:  # noqa: D401
        """Persist a new :class:`AuditLog` instance to the database."""

        log = AuditLog(**data)
        self._session.add(log)
        await self._session.flush()
        return log

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    async def query_logs(
        self,
        *,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        operation: Optional[str] = None,
        page_size: int = 50,
        cursor_timestamp: Optional[str] = None,
        cursor_id: Optional[int] = None,
        asc_order: bool = False,
    ) -> Sequence[AuditLog]:
        """Return audit logs using hybrid cursor pagination strategy."""

        conditions = []
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if entity_id:
            try:
                _eid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
            except ValueError:
                _eid = entity_id  # leave as-is if not valid UUID string
            conditions.append(AuditLog.entity_id == _eid)
        if user_id:
            try:
                _uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            except ValueError:
                _uid = user_id
            conditions.append(AuditLog.user_id == _uid)
        if start_date and end_date:
            conditions.append(
                func.DATE(AuditLog.timestamp).between(start_date, end_date)
            )
        if operation:
            conditions.append(AuditLog.operation == operation)

        # Cursor filter
        if cursor_timestamp and cursor_id:
            conditions.append(
                and_(
                    AuditLog.timestamp > cursor_timestamp,
                    AuditLog.id > cursor_id,
                )
            )

        stmt = select(AuditLog).where(and_(*conditions) if conditions else True)
        order_func = asc if asc_order else desc
        stmt = stmt.order_by(
            order_func(AuditLog.timestamp), order_func(AuditLog.id)
        ).limit(page_size)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list(self, **filters):  # noqa: D401
        """Alias to :meth:`query_logs` for legacy callers."""

        return await self.query_logs(**filters)
