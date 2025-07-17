from pathlib import Path

from tools.fixture_lint.parser import parse_file


def test_parse_file_extracts_fixtures(tmp_path: Path) -> None:
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        """
import pytest

@pytest.fixture
def foo():
    return 1

@pytest.fixture
def bar(foo):
    return foo + 1
"""
    )

    fixtures = parse_file(test_file)
    assert {f.name for f in fixtures} == {"foo", "bar"}

    bar = next(f for f in fixtures if f.name == "bar")
    assert bar.dependencies == ["foo"]
    assert bar.line > 0
