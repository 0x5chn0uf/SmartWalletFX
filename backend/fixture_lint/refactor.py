from __future__ import annotations

from pathlib import Path

import libcst as cst
from libcst import RemovalSentinel

from .duplication import DuplicateGroup


def path_to_module(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


class DeduplicateTransformer(cst.CSTTransformer):
    def __init__(self, fixture_name: str, canonical_module: str) -> None:
        self.fixture_name = fixture_name
        self.canonical_module = canonical_module
        self.removed = False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.BaseStatement | RemovalSentinel:
        if original_node.name.value == self.fixture_name and any(
            self._is_fixture(d) for d in original_node.decorators
        ):
            self.removed = True
            return RemovalSentinel.REMOVE
        return updated_node

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        if not self.removed:
            return updated_node
        import_stmt = cst.parse_statement(
            f"from {self.canonical_module} import {self.fixture_name}\n"
        )
        body = list(updated_node.body)
        # insert import after initial docstring if present
        insert_at = 0
        if (
            body
            and isinstance(body[0], cst.SimpleStatementLine)
            and isinstance(body[0].body[0], cst.Expr)
            and isinstance(body[0].body[0].value, cst.SimpleString)
        ):
            insert_at = 1
        body.insert(insert_at, import_stmt)
        return updated_node.with_changes(body=body)

    @staticmethod
    def _is_fixture(decorator: cst.Decorator) -> bool:
        node = decorator.decorator
        if isinstance(node, cst.Call):
            node = node.func
        if isinstance(node, cst.Attribute):
            return node.attr.value == "fixture"
        if isinstance(node, cst.Name):
            return node.value == "fixture"
        return False


def apply_deduplication(
    groups: list[DuplicateGroup], root: Path, apply: bool = False
) -> None:
    """Deduplicate fixtures in place."""
    for group in groups:
        if len(group.fixtures) < 2:
            continue
        canonical = sorted(group.fixtures, key=lambda f: f.path)[0]
        canonical_module = path_to_module(Path(canonical.path), root)
        for fx in group.fixtures:
            if fx is canonical:
                continue
            path = Path(fx.path)
            code = path.read_text()
            module = cst.parse_module(code)
            transformer = DeduplicateTransformer(fx.name, canonical_module)
            new_module = module.visit(transformer)
            if apply:
                path.write_text(new_module.code)
            else:
                # no-op, but ensures transformation compiles
                new_module.code
