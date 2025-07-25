"""Unit tests for FileUploadService."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.services.file_upload_service import FileUploadError, FileUploadService


class TestFileUploadService:
    """Test FileUploadService functionality."""

    @pytest.fixture
    def mock_audit(self):
        """Mock Audit for testing."""
        return Mock()

    @pytest.fixture
    def temp_upload_dir(self):
        """Create temporary upload directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def service(self, mock_audit, temp_upload_dir):
        """FileUploadService instance for testing."""
        return FileUploadService(mock_audit, upload_dir=temp_upload_dir)

    @pytest.mark.unit
    def test_validate_file_valid_image(self, service, valid_image_file):
        """Test validation passes for allowed image file types."""
        # Should not raise any exception
        service._validate_file(valid_image_file)

    @pytest.mark.unit
    def test_validate_file_invalid_extension(self, service, invalid_image_file):
        """Test validation raises FileUploadError for unsupported file types."""
        with pytest.raises(FileUploadError) as exc_info:
            service._validate_file(invalid_image_file)

        assert exc_info.value.code == "INVALID_EXTENSION"
        assert "File type not allowed" in exc_info.value.message

    @pytest.mark.unit
    def test_validate_file_too_large(self, service, large_image_file):
        """Test validation raises FileUploadError for files exceeding size limit."""
        with pytest.raises(FileUploadError) as exc_info:
            service._validate_file(large_image_file)

        assert exc_info.value.code == "FILE_TOO_LARGE"
        assert "File too large" in exc_info.value.message

    @pytest.mark.unit
    def test_validate_file_no_filename(self, service):
        """Test validation raises FileUploadError when filename is missing."""
        import io

        from fastapi import UploadFile

        file_obj = io.BytesIO(b"content")
        upload_file = UploadFile(filename=None, file=file_obj)

        with pytest.raises(FileUploadError) as exc_info:
            service._validate_file(upload_file)

        assert exc_info.value.code == "NO_FILENAME"
        assert "No filename provided" in exc_info.value.message

    @pytest.mark.unit
    def test_generate_filename_unique(self, service):
        """Test filename generation creates unique filenames preserving extensions."""
        filename1 = service._generate_filename("test.jpg")
        filename2 = service._generate_filename("test.jpg")

        # Should be different (UUID-based)
        assert filename1 != filename2

        # Should preserve extension
        assert filename1.endswith(".jpg")
        assert filename2.endswith(".jpg")

        # Should contain UUID pattern (8-4-4-4-12 characters)
        import re

        uuid_pattern = (
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jpg"
        )
        assert re.match(uuid_pattern, filename1)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_profile_picture_success(
        self, service, valid_image_file, temp_upload_dir
    ):
        """Test successful profile picture upload."""
        user_id = "test-user-123"

        result_url = await service.upload_profile_picture(valid_image_file, user_id)

        # Should return a URL
        assert result_url.startswith("http://localhost:8000/uploads/profile_pictures/")
        assert result_url.endswith(".jpg")

        # File should exist on disk
        filename = result_url.split("/")[-1]
        file_path = Path(temp_upload_dir) / filename
        assert file_path.exists()

        # File content should match
        with open(file_path, "rb") as f:
            content = f.read()
        assert content == b"fake_image_content"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_upload_profile_picture_validation_error(
        self, service, invalid_image_file
    ):
        """Test upload fails with validation error for invalid files."""
        user_id = "test-user-123"

        with pytest.raises(FileUploadError) as exc_info:
            await service.upload_profile_picture(invalid_image_file, user_id)

        assert exc_info.value.code == "INVALID_EXTENSION"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_profile_picture_success(self, service, temp_upload_dir):
        """Test successful profile picture deletion."""
        user_id = "test-user-123"

        # Create a test file
        test_filename = "test-file.jpg"
        test_file_path = Path(temp_upload_dir) / test_filename
        test_file_path.write_bytes(b"test content")

        file_url = f"http://localhost:8000/uploads/profile_pictures/{test_filename}"

        result = await service.delete_profile_picture(file_url, user_id)

        assert result is True
        assert not test_file_path.exists()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_profile_picture_invalid_url(self, service):
        """Test delete raises FileUploadError for invalid URLs."""
        user_id = "test-user-123"
        invalid_url = "http://example.com/invalid/path/file.jpg"

        with pytest.raises(FileUploadError) as exc_info:
            await service.delete_profile_picture(invalid_url, user_id)

        assert exc_info.value.code == "INVALID_URL"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_profile_picture_file_not_found(self, service):
        """Test delete returns False when file doesn't exist."""
        user_id = "test-user-123"
        file_url = "http://localhost:8000/uploads/profile_pictures/nonexistent.jpg"

        result = await service.delete_profile_picture(file_url, user_id)

        assert result is False

    @pytest.mark.unit
    def test_get_file_info_existing(self, service, temp_upload_dir):
        """Test get_file_info returns information for existing files."""
        # Create a test file
        test_filename = "test-info.jpg"
        test_file_path = Path(temp_upload_dir) / test_filename
        test_file_path.write_bytes(b"test content for info")

        file_url = f"http://localhost:8000/uploads/profile_pictures/{test_filename}"

        info = service.get_file_info(file_url)

        assert info is not None
        assert info["filename"] == test_filename
        assert info["size"] == len(b"test content for info")
        assert "created" in info
        assert "modified" in info

    @pytest.mark.unit
    def test_get_file_info_non_existent(self, service):
        """Test get_file_info returns None for non-existent files."""
        file_url = "http://localhost:8000/uploads/profile_pictures/nonexistent.jpg"

        info = service.get_file_info(file_url)

        assert info is None

    @pytest.mark.unit
    def test_get_file_info_invalid_url(self, service):
        """Test get_file_info returns None for invalid URLs."""
        invalid_url = "http://example.com/invalid/path/file.jpg"

        info = service.get_file_info(invalid_url)

        assert info is None
