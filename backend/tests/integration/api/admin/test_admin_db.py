import io
from unittest.mock import patch

from app.api.dependencies import auth_deps
from app.main import app
from app.models.user import User
from fastapi import Depends
from fastapi.testclient import TestClient

client = TestClient(app)


def test_backup_unauthenticated():
    """
    Test that an unauthenticated user cannot access the backup endpoint.
    """
    response = client.post("/admin/db/backup")
    assert response.status_code == 401


@patch("app.tasks.backups.create_backup_task")
def test_backup_authenticated_admin(mock_task):
    """
    Test that an authenticated admin user can trigger a backup.
    """
    # Mock the Celery task to return a fake task ID
    mock_task.delay.return_value.id = "fake-task-id-123"

    # Create a mock user
    mock_user = User(id="test-user-id", username="admin", email="admin@test.com")

    # Override the dependency for this test
    def override_get_current_user():
        return mock_user

    app.dependency_overrides[auth_deps.get_current_user] = override_get_current_user

    try:
        response = client.post("/admin/db/backup")

        assert response.status_code == 202
        assert response.json() == {"task_id": "fake-task-id-123", "status": "accepted"}
        mock_task.delay.assert_called_once()
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


def test_restore_unauthenticated():
    """
    Test that an unauthenticated user cannot access the restore endpoint.
    """
    response = client.post("/admin/db/restore")
    assert response.status_code == 401


@patch("app.tasks.backups.restore_from_upload_task")
def test_restore_authenticated_admin(mock_task):
    """
    Test that an authenticated admin user can trigger a restore.
    """
    # Mock the Celery task to return a fake task ID
    mock_task.delay.return_value.id = "fake-restore-task-id-456"

    # Create a mock user
    mock_user = User(id="test-user-id", username="admin", email="admin@test.com")

    # Override the dependency for this test
    def override_get_current_user():
        return mock_user

    app.dependency_overrides[auth_deps.get_current_user] = override_get_current_user

    try:
        # Create a fake backup file
        fake_backup_content = b"fake backup content"
        files = {
            "file": (
                "backup.sql.gz",
                io.BytesIO(fake_backup_content),
                "application/gzip",
            )
        }

        response = client.post("/admin/db/restore", files=files)

        assert response.status_code == 202
        assert response.json() == {
            "task_id": "fake-restore-task-id-456",
            "status": "accepted",
        }
        mock_task.delay.assert_called_once()
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


@patch("app.tasks.backups.restore_from_upload_task")
def test_restore_invalid_file_type(mock_task):
    """
    Test that uploading a non-.sql.gz file returns a 400 error.
    """
    # Create a mock user
    mock_user = User(id="test-user-id", username="admin", email="admin@test.com")

    # Override the dependency for this test
    def override_get_current_user():
        return mock_user

    app.dependency_overrides[auth_deps.get_current_user] = override_get_current_user

    try:
        # Create a fake file with wrong extension
        fake_content = b"fake content"
        files = {"file": ("backup.txt", io.BytesIO(fake_content), "text/plain")}

        response = client.post("/admin/db/restore", files=files)

        assert response.status_code == 400
        assert "File must be a .sql.gz backup file" in response.json()["detail"]
        mock_task.delay.assert_not_called()
    finally:
        # Clean up the override
        app.dependency_overrides.clear()


@patch("app.tasks.backups.restore_from_upload_task")
def test_restore_missing_file(mock_task):
    """
    Test that a request without a file returns a 422 validation error.
    """
    # Create a mock user
    mock_user = User(id="test-user-id", username="admin", email="admin@test.com")

    # Override the dependency for this test
    def override_get_current_user():
        return mock_user

    app.dependency_overrides[auth_deps.get_current_user] = override_get_current_user

    try:
        response = client.post("/admin/db/restore")

        assert response.status_code == 422  # Validation error
        mock_task.delay.assert_not_called()
    finally:
        # Clean up the override
        app.dependency_overrides.clear()
