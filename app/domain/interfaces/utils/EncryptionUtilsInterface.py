from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class EncryptionUtilsInterface(ABC):
    """Interface for file encryption helpers."""

    @abstractmethod
    def encrypt_file(
        self,
        file_path: Path,
        *,
        recipient: Optional[str] = None,
        gpg_binary: str = "gpg",
    ) -> Path:
        """Encrypt *file_path* and return the encrypted file path."""
