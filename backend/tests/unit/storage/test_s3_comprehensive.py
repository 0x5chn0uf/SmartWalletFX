"""Comprehensive unit tests for S3 storage adapter."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Try to import botocore exceptions, skip tests if not available
try:
    from botocore.exceptions import BotoCoreError, ClientError

    BOTOCORE_AVAILABLE = True
except ImportError:
    BOTOCORE_AVAILABLE = False
    BotoCoreError = Exception
    ClientError = Exception

from app.storage.s3 import S3StorageAdapter


@pytest.mark.skipif(not BOTOCORE_AVAILABLE, reason="botocore not available")
class TestS3StorageAdapter:
    """Test S3 storage adapter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_file_path = Path("/tmp/test_file.txt")
        self.test_bucket = "test-bucket"

    @patch("app.storage.s3.settings")
    @patch("app.storage.s3.boto3")
    def test_init_with_bucket_parameter(self, mock_boto3, mock_settings):
        """Test initialization with explicit bucket parameter."""
        # Set up mock settings with expected values
        mock_settings.AWS_DEFAULT_REGION = "us-east-1"
        mock_settings.AWS_S3_ENDPOINT_URL = None
        mock_settings.AWS_ACCESS_KEY_ID = None
        mock_settings.AWS_SECRET_ACCESS_KEY = None

        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        adapter = S3StorageAdapter(bucket=self.test_bucket)

        assert adapter.bucket == self.test_bucket
        assert adapter._client == mock_client
        mock_boto3.client.assert_called_once_with(
            "s3",
            region_name="us-east-1",
            endpoint_url=None,
            aws_access_key_id=None,
            aws_secret_access_key=None,
        )

    @patch("app.storage.s3.settings")
    @patch("app.storage.s3.boto3")
    def test_init_with_settings_bucket(self, mock_boto3, mock_settings):
        """Test initialization with bucket from settings."""
        mock_settings.BACKUP_S3_BUCKET = self.test_bucket
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        adapter = S3StorageAdapter()

        assert adapter.bucket == self.test_bucket
        assert adapter._client == mock_client

    @patch("app.storage.s3.settings")
    def test_init_no_bucket_configured(self, mock_settings):
        """Test initialization with no bucket configured."""
        mock_settings.BACKUP_S3_BUCKET = None

        with pytest.raises(ValueError, match="S3 bucket name not configured"):
            S3StorageAdapter()

    @patch("app.storage.s3.settings")
    @patch("app.storage.s3.boto3")
    def test_init_with_custom_client(self, mock_boto3, mock_settings):
        """Test initialization with custom client for testing."""
        mock_settings.BACKUP_S3_BUCKET = self.test_bucket
        custom_client = Mock()

        adapter = S3StorageAdapter(client=custom_client)

        assert adapter.bucket == self.test_bucket
        assert adapter._client == custom_client
        # Should not call boto3.client when custom client is provided
        mock_boto3.client.assert_not_called()

    @patch("app.storage.s3.settings")
    @patch("app.storage.s3.boto3")
    def test_init_bucket_parameter_overrides_settings(self, mock_boto3, mock_settings):
        """Test that bucket parameter overrides settings bucket."""
        mock_settings.BACKUP_S3_BUCKET = "settings_bucket"
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        adapter = S3StorageAdapter(bucket=self.test_bucket)

        assert adapter.bucket == self.test_bucket  # Parameter takes precedence
        assert adapter._client == mock_client

    def test_save_success_with_default_destination(self):
        """Test successful file upload with default destination."""
        mock_client = Mock()
        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)

        with patch.object(Path, "exists", return_value=True):
            result = adapter.save(self.test_file_path)

        expected_uri = f"s3://{self.test_bucket}/{self.test_file_path.name}"
        assert result == expected_uri
        mock_client.upload_file.assert_called_once_with(
            str(self.test_file_path), self.test_bucket, self.test_file_path.name
        )

    def test_save_success_with_custom_destination(self):
        """Test successful file upload with custom destination."""
        mock_client = Mock()
        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)
        custom_destination = "backups/2024/01/test_file.txt"

        with patch.object(Path, "exists", return_value=True):
            result = adapter.save(self.test_file_path, destination=custom_destination)

        expected_uri = f"s3://{self.test_bucket}/{custom_destination}"
        assert result == expected_uri
        mock_client.upload_file.assert_called_once_with(
            str(self.test_file_path), self.test_bucket, custom_destination
        )

    def test_save_file_not_found(self):
        """Test save when source file doesn't exist."""
        mock_client = Mock()
        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)

        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                adapter.save(self.test_file_path)

    def test_save_botocore_error(self):
        """Test save when boto3 raises BotoCoreError."""
        mock_client = Mock()
        mock_client.upload_file.side_effect = BotoCoreError()
        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(IOError, match=f"Failed to upload.*{self.test_bucket}"):
                adapter.save(self.test_file_path)

    def test_save_client_error(self):
        """Test save when boto3 raises ClientError."""
        mock_client = Mock()
        mock_client.upload_file.side_effect = ClientError(
            error_response={
                "Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}
            },
            operation_name="UploadFile",
        )
        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(IOError, match=f"Failed to upload.*{self.test_bucket}"):
                adapter.save(self.test_file_path)

    def test_save_error_message_includes_file_and_bucket(self):
        """Test that error message includes file path and bucket name."""
        mock_client = Mock()
        err = BotoCoreError()
        err.args = ("Connection failed",)
        mock_client.upload_file.side_effect = err
        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(IOError) as exc_info:
                adapter.save(self.test_file_path)

            error_message = str(exc_info.value)
            assert str(self.test_file_path) in error_message
            assert self.test_bucket in error_message

    def test_list_success_empty_prefix(self):
        """Test successful listing with empty prefix."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator

        # Mock paginator response
        mock_paginator.paginate.return_value = [
            {"Contents": [{"Key": "file1.txt"}, {"Key": "file2.txt"}]},
            {"Contents": [{"Key": "file3.txt"}]},
        ]

        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)
        result = adapter.list()

        assert result == ["file1.txt", "file2.txt", "file3.txt"]
        mock_client.get_paginator.assert_called_once_with("list_objects_v2")
        mock_paginator.paginate.assert_called_once_with(
            Bucket=self.test_bucket, Prefix=""
        )

    def test_list_success_with_prefix(self):
        """Test successful listing with prefix."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator

        # Mock paginator response
        mock_paginator.paginate.return_value = [
            {"Contents": [{"Key": "backups/file1.txt"}, {"Key": "backups/file2.txt"}]},
        ]

        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)
        result = adapter.list(prefix="backups/")

        assert result == ["backups/file1.txt", "backups/file2.txt"]
        mock_paginator.paginate.assert_called_once_with(
            Bucket=self.test_bucket, Prefix="backups/"
        )

    def test_list_success_empty_bucket(self):
        """Test successful listing of empty bucket."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator

        # Mock paginator response with no contents
        mock_paginator.paginate.return_value = [
            {},  # No Contents key
            {"Contents": []},  # Empty Contents list
        ]

        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)
        result = adapter.list()

        assert result == []

    def test_list_success_sorts_results(self):
        """Test that list results are sorted."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator

        # Mock paginator response with unsorted keys
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "zebra.txt"},
                    {"Key": "alpha.txt"},
                    {"Key": "beta.txt"},
                ]
            },
        ]

        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)
        result = adapter.list()

        assert result == ["alpha.txt", "beta.txt", "zebra.txt"]

    def test_list_botocore_error(self):
        """Test list when boto3 raises BotoCoreError."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = BotoCoreError()

        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)

        with pytest.raises(
            IOError, match=f"Failed to list objects in bucket.*{self.test_bucket}"
        ):
            adapter.list()

    def test_list_client_error(self):
        """Test list when boto3 raises ClientError."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            error_response={
                "Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}
            },
            operation_name="ListObjects",
        )

        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)

        with pytest.raises(
            IOError, match=f"Failed to list objects in bucket.*{self.test_bucket}"
        ):
            adapter.list()

    def test_list_error_message_includes_bucket(self):
        """Test that error message includes bucket name."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        err = BotoCoreError()
        err.args = ("Connection failed",)
        mock_paginator.paginate.side_effect = err

        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)

        with pytest.raises(IOError) as exc_info:
            adapter.list()

        error_message = str(exc_info.value)
        assert self.test_bucket in error_message

    def test_list_handles_missing_contents_key(self):
        """Test that list handles pages without Contents key."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator

        # Mock paginator response with mixed pages
        mock_paginator.paginate.return_value = [
            {"Contents": [{"Key": "file1.txt"}]},  # Has Contents
            {},  # No Contents key
            {"Contents": [{"Key": "file2.txt"}]},  # Has Contents again
        ]

        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)
        result = adapter.list()

        assert result == ["file1.txt", "file2.txt"]

    @patch("app.storage.s3.settings")
    @patch("app.storage.s3.boto3")
    def test_boto3_client_configuration(self, mock_boto3, mock_settings):
        """Test that boto3 client is configured with correct parameters."""
        mock_settings.BACKUP_S3_BUCKET = self.test_bucket
        mock_settings.AWS_DEFAULT_REGION = "us-west-2"
        mock_settings.AWS_S3_ENDPOINT_URL = "https://s3.us-west-2.amazonaws.com"
        mock_settings.AWS_ACCESS_KEY_ID = "test_access_key"
        mock_settings.AWS_SECRET_ACCESS_KEY = "test_secret_key"

        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        S3StorageAdapter()

        mock_boto3.client.assert_called_once_with(
            "s3",
            region_name="us-west-2",
            endpoint_url="https://s3.us-west-2.amazonaws.com",
            aws_access_key_id="test_access_key",
            aws_secret_access_key="test_secret_key",
        )

    def test_save_upload_file_parameters(self):
        """Test that upload_file is called with correct parameters."""
        mock_client = Mock()
        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)

        with patch.object(Path, "exists", return_value=True):
            adapter.save(self.test_file_path, destination="custom/path.txt")

        mock_client.upload_file.assert_called_once_with(
            str(self.test_file_path),  # file_path as string
            self.test_bucket,  # bucket name
            "custom/path.txt",  # destination key
        )

    def test_list_paginator_configuration(self):
        """Test that paginator is configured correctly."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Contents": []}]

        adapter = S3StorageAdapter(bucket=self.test_bucket, client=mock_client)
        adapter.list(prefix="test/")

        mock_client.get_paginator.assert_called_once_with("list_objects_v2")
        mock_paginator.paginate.assert_called_once_with(
            Bucket=self.test_bucket, Prefix="test/"
        )


class TestS3StorageAdapterWithoutBotocore:
    """Test S3 storage adapter when botocore is not available."""

    @pytest.mark.skipif(BOTOCORE_AVAILABLE, reason="botocore is available")
    def test_import_error_when_botocore_not_available(self):
        """Test that S3StorageAdapter raises ImportError when botocore is not available."""
        with pytest.raises(ImportError):
            pass
