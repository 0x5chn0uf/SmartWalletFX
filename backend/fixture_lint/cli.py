from __future__ import annotations

from pathlib import Path

import typer

from .duplication import find_duplicates
from .parser import parse_paths
from .refactor import apply_deduplication
from .report import generate_report

app = typer.Typer(help="Analyze pytest fixtures")


@app.command()
def analyze(path: str = typer.Argument(".")) -> None:
    """Analyze tests under the given path and emit a JSON report."""
    files = [str(p) for p in Path(path).rglob("test_*.py")]
    fixtures = parse_paths(files)
    groups = find_duplicates(fixtures)
    typer.echo(generate_report(fixtures, groups))


@app.command()
def check(path: str = typer.Argument("."), json: bool = False) -> None:
    """Check for duplicate fixtures and fail on detection."""
    files = [str(p) for p in Path(path).rglob("test_*.py")]
    fixtures = parse_paths(files)
    groups = find_duplicates(fixtures)
    if json:
        typer.echo(generate_report(fixtures, groups))
    else:
        for g in groups:
            typer.echo(f"duplicate hash {g.body_hash}:")
            for fx in g.fixtures:
                typer.echo(f"  {fx.path}:{fx.line} {fx.name}")
    if groups:
        raise typer.Exit(code=1)


@app.command()
def deduplicate(path: str = typer.Argument("."), apply: bool = False) -> None:
    """Remove duplicate fixtures by importing from a canonical location."""
    files = [str(p) for p in Path(path).rglob("test_*.py")]
    fixtures = parse_paths(files)
    groups = find_duplicates(fixtures)
    apply_deduplication(groups, Path(path), apply=apply)


if __name__ == "__main__":  # pragma: no cover
    app()
