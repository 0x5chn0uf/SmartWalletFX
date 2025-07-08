from __future__ import annotations

from pathlib import Path

import libcst as cst
from libcst import RemovalSentinel
from libcst.metadata import MetadataWrapper

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


def _extract_imports(path: Path) -> list[str]:
    """Return all import statements from ``path`` preserving order."""
    module = cst.parse_module(path.read_text())
    wrapper = MetadataWrapper(module)
    imports: list[str] = []
    for stmt in module.body:
        if isinstance(stmt, cst.SimpleStatementLine) and isinstance(
            stmt.body[0], (cst.Import, cst.ImportFrom)
        ):
            imports.append(wrapper.module.code_for_node(stmt).rstrip())
    return imports


def apply_deduplication(
    groups: list[DuplicateGroup], root: Path, apply: bool = False
) -> None:
    """Deduplicate fixtures in place and move them to ``tests/fixtures``."""
    base = root.parent if root.name == "tests" else root
    dest_dir = base / "tests" / "fixtures"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "deduplicated.py"
    dest_module = path_to_module(dest_file, base)

    existing_content = dest_file.read_text() if dest_file.exists() else ""
    existing_lines = existing_content.splitlines()
    existing_imports = [
        line
        for line in existing_lines
        if line.startswith("import ") or line.startswith("from ")
    ]
    existing_defs = {
        line.split()[1].split("(")[0]
        for line in existing_lines
        if line.startswith("def ")
    }

    imports: list[str] = existing_imports.copy()
    fixtures_to_add: list[str] = []

    for group in groups:
        if len(group.fixtures) < 2:
            continue
        canonical = sorted(group.fixtures, key=lambda f: f.path)[0]

        if apply and canonical.name not in existing_defs:
            imports.extend(
                [
                    imp
                    for imp in _extract_imports(Path(canonical.path))
                    if imp not in imports
                ]
            )
            fixtures_to_add.append(canonical.body.rstrip() + "\n")

        for fx in group.fixtures:
            path = Path(fx.path)
            code = path.read_text()
            module = cst.parse_module(code)
            transformer = DeduplicateTransformer(canonical.name, dest_module)
            new_module = module.visit(transformer)
            if apply:
                path.write_text(new_module.code)
            else:
                new_module.code

    if apply and fixtures_to_add:
        content_lines = imports + [""] + fixtures_to_add
        dest_file.write_text("\n".join(content_lines).rstrip() + "\n")
