"""Comprehensive unit tests for encryption utilities."""

import subprocess
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import Mock, patch

import pytest

from app.core.config import ConfigurationService
from app.utils.encryption import GPG_BINARY, EncryptionError, encrypt_file


@pytest.fixture
def mock_settings(monkeypatch):
    """Return a proxy whose attribute-writes update ConfigurationService."""

    class _Proxy:
        def __setattr__(self, name, value):
            monkeypatch.setattr(ConfigurationService, name, value, raising=False)

    # Return an instance that test methods can assign to
    return _Proxy()


class TestEncryptionError:
    """Test EncryptionError exception."""

    def test_encryption_error_inheritance(self):
        """Test that EncryptionError inherits from RuntimeError."""
        error = EncryptionError("test error")
        assert isinstance(error, RuntimeError)
        assert str(error) == "test error"


class TestEncryptFile:
    """Test file encryption functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_file_path = Path("/tmp/test_file.txt")
        self.encrypted_path = Path("/tmp/test_file.txt.gpg")

    @patch("app.utils.encryption.subprocess.run")
    def test_encrypt_file_success_with_recipient(self, mock_run):
        """Test successful file encryption with explicit recipient."""
        mock_run.return_value = Mock(returncode=0)

        with patch.object(Path, "exists", return_value=True):
            result = encrypt_file(self.test_file_path, recipient="test_key")

        assert result == self.encrypted_path
        mock_run.assert_called_once_with(
            [
                GPG_BINARY,
                "--batch",
                "--yes",
                "--recipient",
                "test_key",
                "--output",
                str(self.encrypted_path),
                "--encrypt",
                str(self.test_file_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @patch("app.utils.encryption.subprocess.run")
    def test_encrypt_file_success_with_default_recipient(self, mock_run, mock_settings):
        """Test successful file encryption with default recipient from settings."""
        mock_run.return_value = Mock(returncode=0)
        mock_settings.GPG_RECIPIENT_KEY_ID = "default_key"

        with patch.object(Path, "exists", return_value=True):
            result = encrypt_file(self.test_file_path)

        assert result == self.encrypted_path
        mock_run.assert_called_once_with(
            [
                GPG_BINARY,
                "--batch",
                "--yes",
                "--recipient",
                "default_key",
                "--output",
                str(self.encrypted_path),
                "--encrypt",
                str(self.test_file_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @patch("app.utils.encryption.subprocess.run")
    def test_encrypt_file_success_with_custom_gpg_binary(self, mock_run):
        """Test successful file encryption with custom GPG binary."""
        mock_run.return_value = Mock(returncode=0)

        with patch.object(Path, "exists", return_value=True):
            result = encrypt_file(
                self.test_file_path,
                recipient="test_key",
                gpg_binary="/usr/local/bin/gpg",
            )

        assert result == self.encrypted_path
        mock_run.assert_called_once_with(
            [
                "/usr/local/bin/gpg",
                "--batch",
                "--yes",
                "--recipient",
                "test_key",
                "--output",
                str(self.encrypted_path),
                "--encrypt",
                str(self.test_file_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_encrypt_file_file_not_found(self):
        """Test encryption when source file doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                encrypt_file(self.test_file_path, recipient="test_key")

    def test_encrypt_file_no_recipient_configured(self, monkeypatch):
        """Test encryption when no recipient is provided."""
        mock_config = ConfigurationService()
        mock_config.GPG_RECIPIENT_KEY_ID = None
        monkeypatch.setattr("app.utils.encryption.ConfigurationService", lambda: mock_config)
        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(EncryptionError, match="GPG_RECIPIENT_KEY_ID not configured"):
                encrypt_file(self.test_file_path)

    @patch("app.utils.encryption.subprocess.run")
    def test_encrypt_file_gpg_command_failure(self, mock_run):
        """Test encryption when GPG command fails."""
        # Mock CalledProcessError with stderr
        error_output = b"gpg: error: No public key\n"
        mock_run.side_effect = CalledProcessError(
            returncode=2,
            cmd=["gpg", "--batch", "--yes", "--recipient", "test_key"],
            stderr=error_output,
        )

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(EncryptionError, match="gpg: error: No public key"):
                encrypt_file(self.test_file_path, recipient="test_key")

    @patch("app.utils.encryption.subprocess.run")
    def test_encrypt_file_gpg_command_failure_no_stderr(self, mock_run):
        """Test encryption when GPG command fails with no stderr."""
        # Mock CalledProcessError without stderr
        mock_run.side_effect = CalledProcessError(
            returncode=2,
            cmd=["gpg", "--batch", "--yes", "--recipient", "test_key"],
            stderr=None,
        )

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(EncryptionError, match="GPG command failed"):
                encrypt_file(self.test_file_path, recipient="test_key")

    @patch("app.utils.encryption.subprocess.run")
    def test_encrypt_file_gpg_command_failure_stderr_not_bytes(self, mock_run):
        """Test encryption when GPG command fails with non-bytes stderr."""
        # Mock CalledProcessError with string stderr
        mock_run.side_effect = CalledProcessError(
            returncode=2,
            cmd=["gpg", "--batch", "--yes", "--recipient", "test_key"],
            stderr="error message",
        )

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(EncryptionError, match="error message"):
                encrypt_file(self.test_file_path, recipient="test_key")

    @patch("app.utils.encryption.subprocess.run")
    def test_encrypt_file_creates_correct_output_path(self, mock_run):
        """Test that encryption creates the correct output file path."""
        mock_run.return_value = Mock(returncode=0)

        # Test with different file extensions
        test_cases = [
            (Path("/tmp/test.txt"), Path("/tmp/test.txt.gpg")),
            (Path("/tmp/test.sql.gz"), Path("/tmp/test.sql.gz.gpg")),
            (Path("/tmp/test"), Path("/tmp/test.gpg")),
        ]

        for input_path, expected_output in test_cases:
            with patch.object(Path, "exists", return_value=True):
                result = encrypt_file(input_path, recipient="test_key")
                assert result == expected_output

    @patch("app.utils.encryption.subprocess.run")
    def test_encrypt_file_command_arguments(self, mock_run):
        """Test that GPG command is called with correct arguments."""
        mock_run.return_value = Mock(returncode=0)

        with patch.object(Path, "exists", return_value=True):
            encrypt_file(self.test_file_path, recipient="test_key")

        call_args = mock_run.call_args
        cmd = call_args[0][0]

        assert cmd[0] == GPG_BINARY
        assert "--batch" in cmd
        assert "--yes" in cmd
        assert "--recipient" in cmd
        assert "test_key" in cmd
        assert "--output" in cmd
        assert str(self.encrypted_path) in cmd
        assert "--encrypt" in cmd
        assert str(self.test_file_path) in cmd

    @patch("app.utils.encryption.subprocess.run")
    def test_encrypt_file_subprocess_kwargs(self, mock_run):
        """Test that subprocess.run is called with correct kwargs."""
        mock_run.return_value = Mock(returncode=0)

        with patch.object(Path, "exists", return_value=True):
            encrypt_file(self.test_file_path, recipient="test_key")

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["check"] is True
        assert call_kwargs["stdout"] == subprocess.PIPE
        assert call_kwargs["stderr"] == subprocess.PIPE


class TestGPGBinary:
    """Test GPG binary constant."""

    def test_gpg_binary_constant(self):
        """Test that GPG_BINARY is set correctly."""
        assert GPG_BINARY == "gpg"
