from pathlib import Path

from typer.testing import CliRunner

from tools.fixture_lint.cli import app


def test_check_fails_on_duplicates(tmp_path: Path) -> None:
    file_a = tmp_path / "test_a.py"
    file_a.write_text(
        """
import pytest

@pytest.fixture
def foo():
    return 1
"""
    )
    file_b = tmp_path / "test_b.py"
    file_b.write_text(
        """
import pytest

@pytest.fixture
def foo():
    return 1
"""
    )

    runner = CliRunner()
    result = runner.invoke(app, ["check", str(tmp_path)])
    assert result.exit_code == 1
    assert "duplicate hash" in result.output


def test_check_passes_without_duplicates(tmp_path: Path) -> None:
    file_a = tmp_path / "test_a.py"
    file_a.write_text(
        """
import pytest

@pytest.fixture
def foo():
    return 1
"""
    )
    file_b = tmp_path / "test_b.py"
    file_b.write_text(
        """
import pytest

@pytest.fixture
def bar():
    return 1
"""
    )

    runner = CliRunner()
    result = runner.invoke(app, ["check", str(tmp_path)])
    assert result.exit_code == 0


def test_fix_command_merges_duplicates(tmp_path: Path) -> None:
    file_a = tmp_path / "test_a.py"
    file_a.write_text(
        """
import pytest

@pytest.fixture
def foo():
    return 1
"""
    )
    file_b = tmp_path / "test_b.py"
    file_b.write_text(
        """
import pytest

@pytest.fixture
def foo():
    return 1
"""
    )

    runner = CliRunner()
    result = runner.invoke(app, ["fix", str(tmp_path)])
    assert result.exit_code == 0
    metrics = (tmp_path / ".fixture_lint_metrics.json").read_text()
    assert "duplicate_fixtures" in metrics

    dedup_file = tmp_path / "tests" / "fixtures" / "deduplicated.py"
    assert dedup_file.exists()
    expected = "from tests.fixtures.deduplicated import foo"
    assert expected in file_a.read_text()
    assert expected in file_b.read_text()
