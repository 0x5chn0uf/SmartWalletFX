"""File upload service for handling profile pictures and other user files.

Provides secure file upload functionality with validation, storage, and URL generation.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.utils.logging import Audit


class FileUploadError(Exception):
    """Raised when file upload operations fail."""

    def __init__(self, message: str, code: str = "UPLOAD_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class FileUploadService:
    """Service for handling file uploads with validation and storage."""

    # Allowed file extensions for profile pictures
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    # Maximum file size (5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024

    # Upload directory
    UPLOAD_DIR = "uploads/profile_pictures"

    def __init__(
        self,
        audit: Audit,
        base_url: str = "http://localhost:8000",
        upload_dir: str = None,
    ):
        self.__audit = audit
        self.__base_url = base_url.rstrip("/")
        self.upload_dir = upload_dir or self.UPLOAD_DIR
        self._ensure_upload_directory()

    def _ensure_upload_directory(self) -> None:
        """Ensure upload directory exists."""
        upload_path = Path(self.upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)

    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        if not file.filename:
            raise FileUploadError("No filename provided", "NO_FILENAME")

        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            allowed_types = ", ".join(self.ALLOWED_EXTENSIONS)
            raise FileUploadError(
                f"File type not allowed. Allowed types: {allowed_types}",
                "INVALID_EXTENSION",
            )

        # Check file size
        if getattr(file, "size", None) and file.size > self.MAX_FILE_SIZE:
            max_size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise FileUploadError(
                f"File too large. Maximum size: {max_size_mb:.1f}MB",
                "FILE_TOO_LARGE",
            )

    def _generate_filename(self, original_filename: str) -> str:
        """Generate unique filename while preserving extension."""
        file_extension = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"

    async def upload_profile_picture(self, file: UploadFile, user_id: str) -> str:
        """Upload profile picture and return URL."""
        self.__audit.info(
            "profile_picture_upload_started",
            user_id=user_id,
            filename=file.filename,
            content_type=file.content_type,
        )

        try:
            # Validate file
            self._validate_file(file)

            # Generate unique filename
            filename = self._generate_filename(file.filename)
            file_path = Path(self.upload_dir) / filename

            # Save file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # Generate URL
            file_url = f"{self.__base_url}/uploads/profile_pictures/{filename}"

            self.__audit.info(
                "profile_picture_upload_success",
                user_id=user_id,
                filename=filename,
                file_size=len(content),
                url=file_url,
            )

            return file_url

        except FileUploadError:
            self.__audit.warning(
                "profile_picture_upload_validation_failed",
                user_id=user_id,
                filename=file.filename if file.filename else "unknown",
            )
            raise
        except Exception as e:
            self.__audit.error(
                "profile_picture_upload_failed",
                user_id=user_id,
                filename=file.filename if file.filename else "unknown",
                error=str(e),
            )
            raise FileUploadError(f"Upload failed: {str(e)}", "UPLOAD_FAILED")

    async def delete_profile_picture(self, file_url: str, user_id: str) -> bool:
        """Delete profile picture file."""
        self.__audit.info(
            "profile_picture_delete_started",
            user_id=user_id,
            file_url=file_url,
        )

        try:
            # Extract filename from URL
            if not file_url.startswith(f"{self.__base_url}/uploads/profile_pictures/"):
                raise FileUploadError("Invalid file URL", "INVALID_URL")

            filename = file_url.split("/")[-1]
            file_path = Path(self.upload_dir) / filename

            # Delete file if it exists
            if file_path.exists():
                file_path.unlink()
                self.__audit.info(
                    "profile_picture_delete_success",
                    user_id=user_id,
                    filename=filename,
                )
                return True
            else:
                self.__audit.warning(
                    "profile_picture_delete_not_found",
                    user_id=user_id,
                    filename=filename,
                )
                return False

        except FileUploadError:
            # Re-raise FileUploadError (including INVALID_URL) as-is
            raise
        except Exception as e:
            self.__audit.error(
                "profile_picture_delete_failed",
                user_id=user_id,
                file_url=file_url,
                error=str(e),
            )
            raise FileUploadError(f"Delete failed: {str(e)}", "DELETE_FAILED")

    def get_file_info(self, file_url: str) -> Optional[dict]:
        """Get file information from URL."""
        try:
            if not file_url.startswith(f"{self.__base_url}/uploads/profile_pictures/"):
                return None

            filename = file_url.split("/")[-1]
            file_path = Path(self.upload_dir) / filename

            if not file_path.exists():
                return None

            stat = file_path.stat()
            return {
                "filename": filename,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
            }
        except Exception:
            return None
