import hashlib
import os
from pathlib import Path

import pytest

from app.utils.db_backup import (
    _compress_and_hash,
    _hash_file,
    build_pg_dump_cmd,
    build_pg_restore_cmd,
    create_dump,
)


@pytest.fixture(scope="module")
def tmp_output_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("backups")
    return path


def test_build_pg_dump_cmd(tmp_output_dir, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/testdb")

    cmd = build_pg_dump_cmd(tmp_output_dir, label="unit-test")

    # Command should start with pg_dump
    assert cmd[0] == "pg_dump"

    # Ensure --file flag present and points to expected path
    assert "--file" in cmd
    file_index = cmd.index("--file") + 1
    assert cmd[file_index] == str(tmp_output_dir / "unit-test.dump")

    # Ensure DSN is appended as last element
    assert cmd[-1] == "postgresql://localhost/testdb"


def test_build_pg_restore_cmd(tmp_output_dir, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/testdb")

    # Need to create dummy dump file for path existence validation
    dump_path = tmp_output_dir / "unit-test.dump"
    dump_path.touch()

    cmd = build_pg_restore_cmd(dump_path)

    assert cmd[0] == "pg_restore"
    # --dbname should be specified followed by DSN
    assert "--dbname" in cmd
    db_index = cmd.index("--dbname") + 1
    assert cmd[db_index] == "postgresql://localhost/testdb"
    # Last element should be dump path
    assert cmd[-1] == str(dump_path)


def test_compress_and_hash(tmp_output_dir):
    # Create dummy dump file
    raw_path = tmp_output_dir / "dummy.dump"
    raw_content = b"dummy data for hashing\n" * 50
    raw_path.write_bytes(raw_content)

    compressed_path, digest = _compress_and_hash(raw_path)

    assert compressed_path.exists()
    # original file should be removed
    assert not raw_path.exists()

    # digest should equal recomputed digest from uncompressed content
    expected_digest = hashlib.sha256(raw_content).hexdigest()
    assert digest == expected_digest

    # Filename pattern check
    assert compressed_path.suffix == ".gz"
    name_parts = compressed_path.stem.split("_")
    assert len(name_parts) >= 2
    maybe_hash = name_parts[-1]
    # Remove trailing .sql if still present in stem (depends on pathlib version)
    if maybe_hash.endswith(".sql"):
        maybe_hash = maybe_hash[:-4]
    assert len(maybe_hash) == 8


def test_create_dump_success(tmp_output_dir, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/testdb")

    # Stub _run_subprocess to create dummy dump file and return successful CompletedProcess
    from types import SimpleNamespace

    from app.utils import db_backup as mod

    def fake_run(cmd, env=None):
        # get dump path
        idx = cmd.index("--file") + 1
        dump_path = Path(cmd[idx])
        dump_path.write_text("dummy sql")
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(mod, "_run_subprocess", fake_run)

    result_path = create_dump(tmp_output_dir, label="unit-success")

    assert result_path.exists()
    assert result_path.suffix == ".gz"
