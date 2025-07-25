
import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict

from .base import MockBehavior, StatefulMock


class MockFileUploadService(StatefulMock):
    """Enhanced mock file upload service with file tracking."""

    def __init__(self):
        super().__init__()
        self.uploaded_files: Dict[str, Dict[str, Any]] = {}

    async def upload_profile_picture(
        self, user_id: str, file_data: bytes, filename: str
    ) -> str:
        """Mock file upload with realistic behavior."""
        func_name = "upload_profile_picture"

        try:
            if self.behavior == MockBehavior.FAILURE:
                raise ValueError("Upload failed")
            elif self.behavior == MockBehavior.SLOW_RESPONSE:
                await asyncio.sleep(1)  # Simulate slow upload

            # Generate mock file URL
            file_id = str(uuid.uuid4())
            file_url = f"https://storage.example.com/profiles/{file_id}_{filename}"

            # Track uploaded file
            self.uploaded_files[file_url] = {
                "user_id": user_id,
                "filename": filename,
                "size": len(file_data),
                "uploaded_at": datetime.utcnow(),
                "file_id": file_id,
            }

            self.record_call(func_name, (user_id, file_data, filename), {}, file_url)
            return file_url

        except Exception as e:
            self.record_call(func_name, (user_id, file_data, filename), {}, None, e)
            raise

    async def delete_profile_picture(self, file_url: str) -> bool:
        """Mock file deletion."""
        func_name = "delete_profile_picture"

        try:
            if self.behavior == MockBehavior.FAILURE:
                return False

            if file_url in self.uploaded_files:
                del self.uploaded_files[file_url]

            self.record_call(func_name, (file_url,), {}, True)
            return True

        except Exception as e:
            self.record_call(func_name, (file_url,), {}, False, e)
            return False


