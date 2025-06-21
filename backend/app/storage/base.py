import abc
import shutil
from pathlib import Path

from app.core.config import settings


class StorageAdapter(abc.ABC):
    """Protocol for a storage backend."""

    @abc.abstractmethod
    def save(self, file_path: Path, destination: str) -> str:
        """
        Saves a file to the storage backend.

        Args:
            file_path: The local path to the file to save.
            destination: The target path or key in the storage backend.

        Returns:
            A string identifier for the saved file (e.g., path or URL).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def list(self, prefix: str = "") -> list[str]:
        """
        Lists files in the storage backend.

        Args:
            prefix: An optional prefix to filter the file list.

        Returns:
            A list of file identifiers.
        """
        raise NotImplementedError


class LocalStorageAdapter(StorageAdapter):
    """A storage adapter for the local filesystem."""

    def __init__(self, base_dir: Path | str | None = None):
        self.base_dir: Path = (
            Path(base_dir or settings.BACKUP_DIR).expanduser().resolve()
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file_path: Path, destination: str | None = None) -> str:
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        dest_name = destination or file_path.name
        dest_path = self.base_dir / dest_name
        # Prevent directory traversal outside base_dir
        dest_path = dest_path.resolve()
        if not str(dest_path).startswith(str(self.base_dir)):
            raise ValueError("Destination path escapes base directory")

        shutil.copy2(file_path, dest_path)
        return str(dest_path)

    def list(self, prefix: str = "") -> list[str]:
        files: list[str] = []
        for entry in self.base_dir.iterdir():
            if entry.is_file() and entry.name.startswith(prefix):
                files.append(entry.name)
        return sorted(files)
