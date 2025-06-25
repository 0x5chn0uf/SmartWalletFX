import importlib

import pytest


def test_restore_dump_happy(monkeypatch, tmp_path):
    db_backup = importlib.import_module("app.utils.db_backup")

    called = {}

    def fake_run(cmd, *, env=None):
        called["cmd"] = cmd

        class CP:  # dummy completed process
            returncode = 0

        return CP()

    # Ensure DATABASE_URL exists so build_pg_restore_cmd resolves DSN
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    # Patch the _run_subprocess helper
    monkeypatch.setattr(db_backup, "_run_subprocess", fake_run)

    dump_file = tmp_path / "foo.dump"
    dump_file.write_text("dummy")

    db_backup.restore_dump(dump_file, force=True)

    # Assert pg_restore command built correctly
    assert "pg_restore" in called["cmd"][0]
    assert str(dump_file) in called["cmd"][-1]


def test_restore_dump_missing(tmp_path):
    db_backup = importlib.import_module("app.utils.db_backup")
    with pytest.raises(db_backup.RestoreError):
        db_backup.restore_dump(tmp_path / "nonexistent.dump", force=True)
