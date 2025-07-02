from __future__ import annotations

from datetime import datetime

import pytest

from app.models.audit_log import AuditLog


class TestAuditLogUsecase:
    @pytest.mark.asyncio
    async def test_list_audit_logs_basic(self, audit_log_usecase, mock_audit_repo):
        """Test basic audit log listing without filters."""

        # Setup mock response
        mock_logs = [
            AuditLog(
                id=1,
                entity_type="user",
                entity_id="user-1",
                operation="create",
                user_id="admin-1",
                timestamp=datetime(2024, 1, 1, 0, 0, 0),
                changes={},
            ),
            AuditLog(
                id=2,
                entity_type="wallet",
                entity_id="wallet-1",
                operation="update",
                user_id="user-1",
                timestamp=datetime(2024, 1, 2, 0, 0, 0),
                changes={},
            ),
        ]
        mock_audit_repo.query_logs.return_value = mock_logs

        # Call usecase
        result = await audit_log_usecase.list_audit_logs()

        # Verify results
        assert result == mock_logs
        mock_audit_repo.query_logs.assert_called_once_with(
            entity_type=None,
            entity_id=None,
            user_id=None,
            start_date=None,
            end_date=None,
            operation=None,
            page_size=50,
            cursor_timestamp=None,
            cursor_id=None,
            asc_order=False,
        )

    @pytest.mark.asyncio
    async def test_list_audit_logs_with_filters(
        self, audit_log_usecase, mock_audit_repo
    ):
        """Test audit log listing with all filters applied."""
        from datetime import datetime

        # Setup mock response
        mock_logs = [
            AuditLog(
                id=1,
                entity_type="user",
                entity_id="user-1",
                operation="create",
                user_id="admin-1",
                timestamp=datetime(2024, 1, 1, 0, 0, 0),
                changes={},
            ),
        ]
        mock_audit_repo.query_logs.return_value = mock_logs

        # Call usecase with all filters
        result = await audit_log_usecase.list_audit_logs(
            entity_type="users",
            entity_id="123",
            user_id="456",
            start_date="2024-01-01",
            end_date="2024-01-02",
            operation="create",
            page_size=10,
            cursor_timestamp="2024-01-01T00:00:00Z",
            cursor_id=0,
            asc_order=True,
        )

        # Verify results
        assert result == mock_logs
        mock_audit_repo.query_logs.assert_called_once_with(
            entity_type="users",
            entity_id="123",
            user_id="456",
            start_date="2024-01-01",
            end_date="2024-01-02",
            operation="create",
            page_size=10,
            cursor_timestamp="2024-01-01T00:00:00Z",
            cursor_id=0,
            asc_order=True,
        )

    @pytest.mark.asyncio
    async def test_list_audit_logs_empty_result(
        self, audit_log_usecase, mock_audit_repo
    ):
        """Test handling of empty result set."""
        # Setup mock response
        mock_audit_repo.query_logs.return_value = []

        # Call usecase
        result = await audit_log_usecase.list_audit_logs()

        # Verify empty list is returned
        assert result == []
        mock_audit_repo.query_logs.assert_called_once()
