import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("target", ["db-backup", "db-restore"])
def test_make_target_dry_run(target):
    """Ensure the root Makefile delegates backup targets without executing them.

    We invoke `make -n <target>` (dry-run) at the project root and assert the
    printed recipe references the backend Makefile or the Python CLI.  This
    guards against accidental regressions where the target name changes or the
    wrapper is removed.
    """
    # Dynamically locate project root by walking parents until a Makefile is found.
    project_root = next(
        (p for p in Path(__file__).resolve().parents if (p / "Makefile").exists()),
        None,
    )
    assert project_root is not None, "Project root with Makefile not found"

    completed = subprocess.run(
        ["make", "-s", "-n", target], cwd=project_root, capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr

    # The dry-run output should reference either the backend Makefile invocation
    # or the CLI module, depending on nesting level.
    expected_fragments = [
        "make -C",
        "db_backup_cli",
    ]
    assert any(
        fragment in completed.stdout for fragment in expected_fragments
    ), completed.stdout
