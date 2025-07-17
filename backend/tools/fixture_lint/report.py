from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

from .duplication import DuplicateGroup
from .parser import FixtureDefinition


def fixtures_to_dict(fixtures: Iterable[FixtureDefinition]) -> List[dict]:
    return [asdict(fx) for fx in fixtures]


def duplicates_to_dict(groups: Iterable[DuplicateGroup]) -> List[dict]:
    data = []
    for g in groups:
        data.append(
            {
                "hash": g.body_hash,
                "fixtures": fixtures_to_dict(g.fixtures),
            }
        )
    return data


def generate_report(
    fixtures: Iterable[FixtureDefinition], groups: Iterable[DuplicateGroup]
) -> str:
    report = {
        "fixtures": fixtures_to_dict(fixtures),
        "duplicates": duplicates_to_dict(groups),
    }
    return json.dumps(report, indent=2)


def write_metrics(
    fixtures: Iterable[FixtureDefinition],
    groups: Iterable[DuplicateGroup],
    path: str | Path,
) -> None:
    """Write basic metrics about the analysed fixtures to a JSON file."""
    total = len(list(fixtures))
    duplicates = sum(len(g.fixtures) for g in groups)
    data = {
        "total_fixtures": total,
        "duplicate_fixtures": duplicates,
        "duplicate_groups": len(groups),
    }
    Path(path).write_text(json.dumps(data, indent=2))
