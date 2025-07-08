from __future__ import annotations

import json
from dataclasses import asdict
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
