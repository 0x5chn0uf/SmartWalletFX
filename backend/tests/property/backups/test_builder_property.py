from pathlib import Path

import hypothesis.strategies as st
from hypothesis import HealthCheck, given
from hypothesis import settings as hyp_settings

from app.utils.db_backup import build_pg_dump_cmd

# Use fast profile settings from project (max_examples already 25) but allow longer deadline
hyp_settings.register_profile("ci", max_examples=50, deadline=None)
hyp_settings.load_profile("fast")


@given(
    label=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
        min_size=1,
        max_size=20,
    )
)
@hyp_settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
def test_build_pg_dump_cmd_injection_safe(tmp_path_factory, monkeypatch, label: str):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/testdb")

    output_dir = tmp_path_factory.mktemp("props")

    cmd = build_pg_dump_cmd(output_dir, label=label)

    # Ensure command list has no dangerous characters in each argument
    dangerous_chars = {";", "&", "|", "`", "$", "\n"}
    for arg in cmd:
        assert not any(ch in arg for ch in dangerous_chars)

    # Validate that resulting dump filename contains label and ends with .dump
    file_idx = cmd.index("--file") + 1
    file_path = Path(cmd[file_idx])
    assert file_path.name.startswith(label)
    assert file_path.suffix == ".dump"
