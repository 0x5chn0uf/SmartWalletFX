from pathlib import Path

import pytest

from app.storage import get_storage_adapter
from app.storage.base import LocalStorageAdapter


def test_get_storage_adapter_local(tmp_path: Path):
    """Factory yields LocalStorageAdapter and basic operations succeed."""
    adapter = get_storage_adapter("local")
    assert isinstance(adapter, LocalStorageAdapter)

    src_file = tmp_path / "dummy.txt"
    src_file.write_text("hello")

    saved_path = Path(adapter.save(src_file))
    assert saved_path.exists()
    assert saved_path.read_text() == "hello"

    assert "dummy.txt" in adapter.list(prefix="dummy")


def test_get_storage_adapter_unknown():
    """Unknown adapter id raises ValueError."""
    with pytest.raises(ValueError):
        get_storage_adapter("unknown")
