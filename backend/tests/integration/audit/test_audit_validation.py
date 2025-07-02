from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_invalid_login_emits_valid_audit_event(
    async_client_with_db: AsyncClient,
) -> None:
    """Call /auth/token with wrong credentials.

    The audit-validator plugin should automatically check the emitted AUDIT log
    entry for structural validity.  We only assert the HTTP status code here –
    plugin failures will surface as test failures if validation fails.
    """

    response = await async_client_with_db.post(
        "/auth/token",
        data={"username": "nonexistent", "password": "WrongPwd123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
