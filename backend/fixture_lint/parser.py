from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import libcst as cst
from libcst.metadata import PositionProvider


@dataclass
class FixtureDefinition:
    """Information about a pytest fixture."""

    name: str
    path: str
    line: int
    dependencies: List[str]
    body: str


def _is_fixture_decorator(decorator: cst.Decorator) -> bool:
    node = decorator.decorator
    if isinstance(node, cst.Call):
        node = node.func
    if isinstance(node, cst.Attribute):
        return node.attr.value == "fixture"
    if isinstance(node, cst.Name):
        return node.value == "fixture"
    return False


def parse_file(path: str | Path) -> List[FixtureDefinition]:
    """Parse a Python file and return all fixture definitions."""
    file_path = Path(path)
    module = cst.parse_module(file_path.read_text())
    wrapper = cst.metadata.MetadataWrapper(module)
    positions = wrapper.resolve(PositionProvider)

    fixtures: List[FixtureDefinition] = []
    for node in wrapper.module.body:
        if isinstance(node, cst.FunctionDef):
            if any(_is_fixture_decorator(d) for d in node.decorators):
                params = [p.name.value for p in node.params.params]
                params += [p.name.value for p in node.params.kwonly_params]
                if node.params.posonly_params:
                    params += [p.name.value for p in node.params.posonly_params]
                pos = positions[node]
                body = wrapper.module.code_for_node(node)
                fixtures.append(
                    FixtureDefinition(
                        name=node.name.value,
                        path=str(file_path),
                        line=pos.start.line,
                        dependencies=params,
                        body=body,
                    )
                )
    return fixtures


def parse_paths(paths: Iterable[str | Path]) -> List[FixtureDefinition]:
    """Parse multiple files for fixture definitions."""
    result: List[FixtureDefinition] = []
    for p in paths:
        result.extend(parse_file(p))
    return result
