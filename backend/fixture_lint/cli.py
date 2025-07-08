from __future__ import annotations

from pathlib import Path

import typer

from .duplication import find_duplicates
from .parser import parse_paths
from .refactor import apply_deduplication
from .report import generate_report

app = typer.Typer(help="Analyze pytest fixtures")


@app.command()
def analyze(path: str = ".") -> None:
    """Analyze tests under the given path and emit a JSON report."""
    files = [str(p) for p in Path(path).rglob("test_*.py")]
    fixtures = parse_paths(files)
    groups = find_duplicates(fixtures)
    typer.echo(generate_report(fixtures, groups))


@app.command()
def deduplicate(path: str = ".", apply: bool = False) -> None:
    """Remove duplicate fixtures by importing from a canonical location."""
    files = [str(p) for p in Path(path).rglob("test_*.py")]
    fixtures = parse_paths(files)
    groups = find_duplicates(fixtures)
    apply_deduplication(groups, Path(path), apply=apply)


if __name__ == "__main__":  # pragma: no cover
    app()
