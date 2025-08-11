from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, Iterable, List

from .parser import FixtureDefinition


@dataclass
class DuplicateGroup:
    """Group of fixtures with identical bodies."""

    body_hash: str
    fixtures: List[FixtureDefinition]


def find_duplicates(fixtures: Iterable[FixtureDefinition]) -> List[DuplicateGroup]:
    """Return groups of fixtures that share the same body."""
    by_hash: Dict[str, List[FixtureDefinition]] = {}
    for fx in fixtures:
        h = hashlib.sha1(fx.body.encode("utf-8")).hexdigest()
        by_hash.setdefault(h, []).append(fx)

    groups = [DuplicateGroup(h, fxs) for h, fxs in by_hash.items() if len(fxs) > 1]
    return groups
