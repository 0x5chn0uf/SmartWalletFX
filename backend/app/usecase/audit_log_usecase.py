from __future__ import annotations

from typing import Optional, Sequence

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogUsecase:
    """Use case for audit log operations, encapsulating business logic
    and data access."""

    def __init__(self, repo: AuditLogRepository) -> None:
        self._repo = repo

    async def list_audit_logs(
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
        """Return paginated audit logs through repository using hybrid pagination."""
        return await self._repo.query_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            operation=operation,
            page_size=page_size,
            cursor_timestamp=cursor_timestamp,
            cursor_id=cursor_id,
            asc_order=asc_order,
        )
