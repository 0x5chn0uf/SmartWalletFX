import uuid
from datetime import datetime, timedelta

import pytest

from app.repositories.audit_log_repository import AuditLogRepository


@pytest.mark.asyncio
async def test_audit_log_repository_list_filters(db_session):
    """Ensure `list()` (alias to `query_logs`) correctly filters and orders logs."""

    repo = AuditLogRepository(db_session)

    user_id = uuid.uuid4().hex
    other_user_id = uuid.uuid4().hex

    # Create three logs with varying attributes
    log1 = await repo.create(
        entity_type="users",
        entity_id=user_id,
        operation="create",
        changes={"username": "alice"},
        user_id=user_id,
        timestamp=datetime.utcnow() - timedelta(minutes=2),
    )
    log2 = await repo.create(
        entity_type="users",
        entity_id=user_id,
        operation="update",
        changes={"username": {"old": "alice", "new": "alice2"}},
        user_id=user_id,
        timestamp=datetime.utcnow() - timedelta(minutes=1),
    )
    _ = await repo.create(
        entity_type="wallets",
        entity_id="wallet-123",
        operation="create",
        changes={"address": "0xabc"},
        user_id=other_user_id,
        timestamp=datetime.utcnow(),
    )

    await db_session.commit()

    # Filter by entity_type and entity_id should return only the first two logs
    logs = await repo.list(entity_type="users", entity_id=user_id, asc_order=True)
    assert logs == [log1, log2]

    # Filter by user_id should return both user-related logs
    logs_by_user = await repo.list(user_id=user_id)
    assert set(logs_by_user) == {log1, log2}

    # Pagination – request first item in ascending order
    first_page = await repo.list(
        entity_type="users", entity_id=user_id, asc_order=True, page_size=1
    )
    assert first_page == [log1]
