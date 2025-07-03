from pathlib import Path

import hypothesis.strategies as st
from hypothesis import HealthCheck, given
from hypothesis import settings as hyp_settings

from app.utils.db_backup import build_pg_restore_cmd

# Use fast profile settings from project (max_examples already 25) but allow longer deadline
hyp_settings.register_profile("ci", max_examples=50, deadline=None)
hyp_settings.load_profile("fast")


@given(
    filename=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
        min_size=1,
        max_size=20,
    )
)
@hyp_settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
def test_build_pg_restore_cmd_injection_safe(
    tmp_path_factory, monkeypatch, filename: str
):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/testdb")

    dump_dir = tmp_path_factory.mktemp("props")
    dump_path = dump_dir / f"{filename}.dump"
    dump_path.touch()

    cmd = build_pg_restore_cmd(dump_path)

    # Ensure command list has no dangerous characters in each argument
    dangerous_chars = {";", "&", "|", "`", "\n", "$"}
    for arg in cmd:
        assert not any(ch in arg for ch in dangerous_chars)

    # Validate command contains --dbname followed by DSN and ends with dump path
    db_index = cmd.index("--dbname") + 1
    assert cmd[db_index] == "postgresql://localhost/testdb"
    assert cmd[-1] == str(dump_path)
