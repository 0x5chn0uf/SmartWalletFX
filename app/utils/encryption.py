"""GPG encryption utilities.

The helpers here are intentionally minimal and invoke the system `gpg` binary
via :pymod:`subprocess`.  We purposely avoid a heavy dependency on
``python-gnupg`` for the encryption *caller* to keep the runtime footprint
small when encryption is turned *off*.  The library is only required when
advanced functionality (key-management, decryption) is needed.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final, Optional

from app.core.config import Configuration
from app.domain.interfaces.utils import EncryptionUtilsInterface

__all__: Final[list[str]] = [
    "EncryptionError",
    "EncryptionUtils",
]


class EncryptionError(RuntimeError):
    """Raised when GPG encryption fails."""


GPG_BINARY: Final[str] = "gpg"


class EncryptionUtils(EncryptionUtilsInterface):
    """Utility class for GPG encryption operations."""

    def __init__(self, config: Configuration):
        """Initialize EncryptionUtils with dependencies."""
        self.__config = config

    def encrypt_file(
        self,
        file_path: Path,
        *,
        recipient: Optional[str] = None,
        gpg_binary: str = GPG_BINARY,
    ) -> Path:
        """Encrypt *file_path* using GPG *--recipient* public-key encryption.

        Returns the path to the encrypted file (original file is **not** removed).
        """

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        recipient_key = recipient or self.__config.GPG_RECIPIENT_KEY_ID
        if not recipient_key:
            raise EncryptionError("GPG_RECIPIENT_KEY_ID not configured")

        encrypted_path = file_path.with_suffix(file_path.suffix + ".gpg")

        cmd = [
            gpg_binary,
            "--batch",
            "--yes",
            "--recipient",
            recipient_key,
            "--output",
            str(encrypted_path),
            "--encrypt",
            str(file_path),
        ]

        try:
            subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as exc:
            if exc.stderr is None:
                error_msg = "GPG command failed"
            elif isinstance(exc.stderr, bytes):
                error_msg = exc.stderr.decode().strip()
            else:
                error_msg = str(exc.stderr).strip()
            raise EncryptionError(error_msg) from exc

        return encrypted_path
