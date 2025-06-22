from __future__ import annotations

from app.core.config import settings

from .base import LocalStorageAdapter, StorageAdapter

__all__ = [
    "get_storage_adapter",
]


def get_storage_adapter(name: str | None = None) -> StorageAdapter:  # noqa: D401
    """Return a configured StorageAdapter instance.

    If *name* is None, the adapter is resolved from settings.BACKUP_STORAGE_ADAPTER.
    """

    adapter_name = (name or settings.BACKUP_STORAGE_ADAPTER).lower()
    if adapter_name == "local":
        return LocalStorageAdapter()

    # S3 adapter placeholder – will be implemented in a later step
    if adapter_name == "s3":  # pragma: no cover
        from .s3 import S3StorageAdapter  # late import to avoid optional dep

        return S3StorageAdapter()

    raise ValueError(f"Unknown storage adapter: {adapter_name}")
