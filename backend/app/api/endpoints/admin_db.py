import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import auth_deps
from app.models.user import User

router = APIRouter()


@router.post(
    "/backup",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a database backup (admin only)",
)
async def trigger_backup(
    current_user: User = Depends(auth_deps.get_current_user),
):
    """Trigger an asynchronous database backup via Celery.

    Requires an authenticated user with admin privileges (enforced elsewhere).
    Returns a Celery task identifier so the caller can poll for status.
    """

    # Admin check -------------------------------------------------------
    if not hasattr(current_user, "roles") or "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
        )

    # Import inside function to avoid circular dependencies at import time
    from app.tasks.backups import create_backup_task  # pragma: no cover

    task = create_backup_task.delay()
    return {"task_id": task.id, "status": "accepted"}


@router.post(
    "/restore",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Restore database from backup file (admin only)",
)
async def trigger_restore(
    file: UploadFile = File(...),
    current_user: User = Depends(auth_deps.get_current_user),
):
    """Trigger an asynchronous database restore via Celery.

    Accepts a .sql.gz backup file upload and processes it in the background.
    Requires an authenticated user with admin privileges.
    Returns a Celery task identifier so the caller can poll for status.
    """

    # Admin check -------------------------------------------------------
    if not hasattr(current_user, "roles") or "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
        )

    # Validate file type
    if not file.filename or not file.filename.endswith(".sql.gz"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .sql.gz backup file",
        )

    # Save uploaded file to temporary location
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sql.gz")
    try:
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # Import inside function to avoid circular dependencies at import time
        from app.tasks.backups import (
            restore_from_upload_task,  # pragma: no cover
        )

        task = restore_from_upload_task.delay(temp_file.name)
        return {"task_id": task.id, "status": "accepted"}

    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}",
        )
