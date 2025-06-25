import pytest

from app.utils import db_backup as mod


def test_build_pg_dump_cmd_missing_dir(tmp_path):
    # Provide path that has been removed to trigger FileNotFoundError
    missing_dir = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError):
        mod.build_pg_dump_cmd(missing_dir, label="fail")


def test_create_dump_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/testdb")

    # Monkeypatch subprocess runner to fail
    def fake_run(cmd, env=None):
        raise RuntimeError("pg_dump failed")

    monkeypatch.setattr(mod, "_run_subprocess", fake_run)

    with pytest.raises(mod.BackupError):
        mod.create_dump(tmp_path, label="fail")
