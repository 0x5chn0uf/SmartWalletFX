import importlib
from pathlib import Path


def test_cli_restore_guard(tmp_path):
    cli = importlib.import_module("app.cli.db_backup_cli")
    dump = tmp_path / "dummy.sql.gz"
    dump.write_text("x")

    # without --force in production should exit code 2
    code = cli.main(["restore", str(dump), "--env", "production"])
    assert code == 2


def test_cli_restore_invokes(monkeypatch, tmp_path):
    called = {}

    def fake_restore_dump(
        dump_path: Path, *, force: bool, target_db_url=None, env=None
    ):
        called["dump_path"] = dump_path
        called["force"] = force

    monkeypatch.setattr("app.utils.db_backup.restore_dump", fake_restore_dump)

    cli = importlib.import_module("app.cli.db_backup_cli")
    dump = tmp_path / "dummy.sql.gz"
    dump.write_text("x")

    code = cli.main(
        [
            "restore",
            str(dump),
            "--env",
            "production",
            "--force",
        ]
    )
    assert code == 0
    assert called["dump_path"] == dump
    assert called["force"] is True
