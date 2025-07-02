"""Audit Logs API endpoint.

Provides secure access to audit trail entries with cursor pagination.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.api import dependencies as deps
from app.api.dependencies import require_roles
from app.core.security.roles import UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.usecase.audit_log_usecase import AuditLogUsecase

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


class AuditLogOut(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    operation: str
    user_id: str
    timestamp: datetime
    changes: dict[str, object] = Field(..., description="Entity-specific change data")

    class Config:
        orm_mode = True


class PaginatedAuditLogs(BaseModel):
    results: list[AuditLogOut]
    next_cursor: Optional[str]


@router.get(
    "",
    response_model=PaginatedAuditLogs,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([UserRole.ADMIN.value]))],
)
async def list_audit_logs(
    entity_type: Annotated[
        Optional[str], Query(description="Filter by entity type")
    ] = None,
    entity_id: Annotated[
        Optional[str], Query(description="Filter by entity id")
    ] = None,
    user_id: Annotated[Optional[str], Query(description="Filter by user id")] = None,
    start_date: Annotated[Optional[datetime], Query()] = None,
    end_date: Annotated[Optional[datetime], Query()] = None,
    operation: Annotated[Optional[str], Query()] = None,
    cursor: Annotated[Optional[str], Query(description="Pagination cursor")] = None,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    asc: Annotated[bool, Query(description="Ascending order flag")] = False,
    session=Depends(deps.get_db),
    _=Depends(deps.auth_deps.get_current_user),
):
    """Return paginated audit logs with optional filters.

    The *cursor* is a base64-encoded string generated from the last item's
    `(timestamp, id)` pair to support efficient pagination.
    """

    usecase = AuditLogUsecase(AuditLogRepository(session))

    cursor_timestamp = None
    cursor_id = None
    if cursor:
        from base64 import b64decode

        try:
            ts_str, id_str = b64decode(cursor.encode()).decode().split(":")
            cursor_timestamp = datetime.fromisoformat(ts_str)
            cursor_id = int(id_str)
        except Exception:  # noqa: BLE001
            cursor_timestamp = None
            cursor_id = None

    logs = await usecase.list_audit_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None,
        operation=operation,
        page_size=page_size,
        cursor_timestamp=cursor_timestamp,
        cursor_id=cursor_id,
        asc_order=asc,
    )

    next_cursor = None
    if logs:
        last = logs[-1]
        from base64 import b64encode

        cursor_raw = f"{last.timestamp.isoformat()}:{last.id}"
        next_cursor = b64encode(cursor_raw.encode()).decode()

    return PaginatedAuditLogs(
        results=[AuditLogOut.from_orm(log) for log in logs],
        next_cursor=next_cursor,
    )
