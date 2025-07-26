from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from fastapi import UploadFile


class FileUploadServiceInterface(ABC):
    """Interface for file upload operations."""

    @abstractmethod
    async def upload_profile_picture(self, file: UploadFile, user_id: str) -> str:
        """Upload a profile picture and return its URL."""

    @abstractmethod
    async def delete_profile_picture(self, file_url: str, user_id: str) -> bool:
        """Delete a profile picture by URL."""

    @abstractmethod
    def get_file_info(self, file_url: str) -> Optional[dict]:
        """Return information about an uploaded file or ``None``."""
