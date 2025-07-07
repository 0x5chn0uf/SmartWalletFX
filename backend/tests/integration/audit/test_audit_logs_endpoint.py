import base64
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_audit_logs_pagination_and_cursor(
    admin_authenticated_client: AsyncClient, monkeypatch
) -> None:
    """Verify that /audit-logs returns expected data & next_cursor handling."""

    from app.api.endpoints import audit_logs as al_ep

    class _DummyLog:  # noqa: D101 – simple struct
        def __init__(self, _id: int, ts: datetime):
            self.id = _id
            self.entity_type = "wallet"
            self.entity_id = "123"
            self.operation = "create"
            self.user_id = "admin"
            self.timestamp = ts
            self.changes = {"field": "value"}

    now = datetime.utcnow()
    sample_logs = [_DummyLog(i, now + timedelta(seconds=i)) for i in range(3)]

    async def _dummy_list(self, **kwargs):  # noqa: D401 – stub
        # Ensure filters/kwargs are passed through without errors
        assert "page_size" in kwargs
        return sample_logs

    # Patch use-case method with dummy implementation
    monkeypatch.setattr(
        al_ep.AuditLogUsecase, "list_audit_logs", _dummy_list, raising=False
    )

    resp = await admin_authenticated_client.get("/audit-logs?page_size=3&asc=true")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["results"]) == 3
    # next_cursor should be a base64 string
    assert body["next_cursor"]
    # Decode cursor to ensure correct format (<iso-ts>:<id>)
    ts_str, _id = base64.b64decode(body["next_cursor"].encode()).decode().split(":")
    # should match last log
    assert ts_str.startswith(now.date().isoformat()[:10])
    assert _id == str(sample_logs[-1].id)

    # Invalid cursor must be gracefully ignored (no 400)
    bad = await admin_authenticated_client.get("/audit-logs?cursor=invalid$$$")
    assert bad.status_code == 200
    assert bad.json()["results"]  # still returns data
