import os
from pathlib import Path

import pytest

from app.core import config as config_module
from app.storage.base import StorageAdapter
from app.utils import db_backup


class _DummyAdapter(StorageAdapter):
    def __init__(self):
        self.saved: list[tuple[Path, str | None]] = []

    def save(
        self, file_path: Path, destination: str | None = None
    ) -> str:  # noqa: D401
        self.saved.append((file_path, destination))
        return f"dummy://{destination or file_path.name}"

    def list(self, prefix: str = ""):  # noqa: D401
        return [
            s[1] or s[0].name
            for s in self.saved
            if (s[1] or s[0].name).startswith(prefix)
        ]


@pytest.mark.usefixtures("tmp_path")
def test_create_dump_with_encryption_and_upload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """create_dump encrypts file and uploads via adapter when enabled."""

    # Enable encryption & set adapter
    monkeypatch.setattr(config_module.settings, "BACKUP_ENCRYPTION_ENABLED", True)

    monkeypatch.setitem(
        os.environ, "DATABASE_URL", "postgresql://user:pass@localhost/db"
    )

    dummy_adapter = _DummyAdapter()

    # Patch factory to return dummy adapter
    monkeypatch.setitem(os.environ, "DUMMY", "1")  # ensure env exists

    import importlib

    from app import storage as storage_pkg  # noqa: WPS433

    monkeypatch.setattr(
        storage_pkg, "get_storage_adapter", lambda name=None: dummy_adapter
    )
    monkeypatch.setattr(
        "app.utils.db_backup.get_storage_adapter", lambda: dummy_adapter
    )

    # Patch encrypt_file to just append .gpg extension
    def _fake_encrypt(file_path: Path, *_, **__):  # noqa: D401
        encrypted = file_path.with_suffix(file_path.suffix + ".gpg")
        encrypted.write_bytes(file_path.read_bytes())
        return encrypted

    monkeypatch.setattr("app.utils.encryption.encrypt_file", _fake_encrypt)
    monkeypatch.setattr("app.utils.db_backup.encrypt_file", _fake_encrypt)

    # Call create_dump with a small dummy file: instead of calling pg_dump, we monkeypatch subprocess
    def _fake_run(cmd, **kwargs):  # noqa: D401
        # create dummy dump file at --file index
        file_idx = cmd.index("--file") + 1
        dump_path = Path(cmd[file_idx])
        dump_path.write_text("dummy sql")
        return None

    monkeypatch.setattr("app.utils.db_backup._run_subprocess", _fake_run)

    # Run create_dump
    result_path = db_backup.create_dump(tmp_path, compress=False)

    # Assertions
    assert result_path.suffix.endswith(".gpg")
    # adapter.save called once
    assert len(dummy_adapter.saved) == 1
    saved_path, _dest = dummy_adapter.saved[0]
    assert saved_path == result_path

    # Clean up
    # os.remove(result_path)
    # os.remove(dump_path)
