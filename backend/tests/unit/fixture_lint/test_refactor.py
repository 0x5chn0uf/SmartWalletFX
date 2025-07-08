from pathlib import Path

from fixture_lint.duplication import find_duplicates
from fixture_lint.parser import parse_paths
from fixture_lint.refactor import apply_deduplication


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

    assert "from test_a import foo" in file_b.read_text()
    # original fixture removed
    assert "@pytest.fixture" not in file_b.read_text()
