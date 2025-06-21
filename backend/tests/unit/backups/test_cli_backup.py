import importlib
from pathlib import Path


def test_cli_backup_invokes_create_dump(monkeypatch, tmp_path):
    called = {}

    def fake_create_dump(output_dir: Path, *, compress: bool, label=None, env=None):
        called["output_dir"] = output_dir
        called["label"] = label
        return output_dir / "dummy.sql.gz"

    monkeypatch.setattr("app.utils.db_backup.create_dump", fake_create_dump)

    cli = importlib.import_module("app.cli.db_backup_cli")
    code = cli.main(["backup", "--output-dir", str(tmp_path), "--label", "mylbl"])
    assert code == 0
    assert called["output_dir"] == tmp_path
    assert called["label"] == "mylbl"
