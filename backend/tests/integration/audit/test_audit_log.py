from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from tests.utils.auth import create_authenticated_user


@pytest.mark.asyncio
async def test_audit_log_on_user_crud(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that user CRUD operations generate audit logs."""

    # 1. Create and authenticate a user
    user, headers = await create_authenticated_user(
        db_session, async_client, email="audit_test@example.com", password="testpass123"
    )

    # 2. Update the user
    update_data = {
        "username": "new_username_audited",
        "email": "audit_test@example.com",
        "password": "testpass123",
    }
    update_response = await async_client.put(
        f"/users/{user.id}", json=update_data, headers=headers
    )
    assert update_response.status_code == 200, update_response.text

    # 3. Delete the user directly via repository (avoids FK constraint conflicts)
    user_repo = UserRepository(db_session)
    await user_repo.delete(user)

    # 4. Verify audit logs were created
    audit_repo = AuditLogRepository(db_session)
    logs = await audit_repo.list(entity_id=str(user.id), entity_type="users")

    # Should have 3 logs: create, update, delete
    assert len(logs) == 3, f"Expected 3 audit logs, got {len(logs)}"

    # Verify log details
    create_log = next(log for log in logs if log.operation == "create")
    update_log = next(log for log in logs if log.operation == "update")
    delete_log = next(log for log in logs if log.operation == "delete")

    assert create_log.entity_type == "users"
    assert create_log.entity_id == str(user.id)
    assert create_log.user_id == str(user.id)
    assert "username" in create_log.changes
    assert "email" in create_log.changes

    assert update_log.entity_type == "users"
    assert update_log.entity_id == str(user.id)
    assert update_log.user_id == str(user.id)
    assert update_log.changes["username"]["old"] == "audit_test@example.com"
    assert update_log.changes["username"]["new"] == "new_username_audited"

    assert delete_log.entity_type == "users"
    assert delete_log.entity_id == str(user.id)
    assert delete_log.user_id == str(user.id)
