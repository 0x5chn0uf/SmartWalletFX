from pathlib import Path

import pytest

from tools.fixture_lint.duplication import find_duplicates
from tools.fixture_lint.parser import parse_paths
from tools.fixture_lint.refactor import apply_deduplication


@pytest.mark.unit
def test_apply_deduplication(tmp_path: Path) -> None:
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

    fixtures = parse_paths([file_a, file_b])
    groups = find_duplicates(fixtures)
    apply_deduplication(groups, tmp_path, apply=True)

    dedup_file = tmp_path / "tests" / "fixtures" / "deduplicated.py"
    assert dedup_file.exists()
    assert "def foo" in dedup_file.read_text()

    # both files now import from the shared fixture
    expected = "from tests.fixtures.deduplicated import foo"
    assert expected in file_a.read_text()
    assert expected in file_b.read_text()
