from pathlib import Path

from fixture_lint.duplication import find_duplicates
from fixture_lint.parser import parse_paths


def test_find_duplicates(tmp_path: Path) -> None:
    file1 = tmp_path / "test_a.py"
    file1.write_text(
        """
import pytest

@pytest.fixture
def foo():
    return 42
"""
    )

    file2 = tmp_path / "test_b.py"
    file2.write_text(
        """
import pytest

@pytest.fixture
def foo():
    return 42
"""
    )

    fixtures = parse_paths([file1, file2])
    dups = find_duplicates(fixtures)
    assert len(dups) == 1
    assert len(dups[0].fixtures) == 2
    names = {fx.name for fx in dups[0].fixtures}
    assert names == {"foo"}
