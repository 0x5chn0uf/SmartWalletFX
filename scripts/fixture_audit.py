#!/usr/bin/env python3
"""
AST-based Fixture Audit Script for Task 114

This script analyzes the backend test suite to catalog all existing fixtures,
identify duplications and inconsistencies, and document which fixtures are
linked to specific test modules. Uses Python's ast module for robust parsing.

Usage:
    python scripts/fixture_audit.py
"""

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


class FixtureVisitor(ast.NodeVisitor):
    def __init__(self):
        self.fixtures = {}
        self.test_functions = {}
        self.imported_fixtures = set()

    def visit_FunctionDef(self, node):
        # Check for @pytest.fixture decorator
        fixture_decorator = None
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and getattr(decorator.func, "attr", None) == "fixture"
            ):
                fixture_decorator = decorator
            elif isinstance(decorator, ast.Attribute) and decorator.attr == "fixture":
                fixture_decorator = decorator
        if fixture_decorator:
            # Extract fixture details
            fixture_name = node.name
            scope = "function"
            autouse = False
            params = []
            if isinstance(fixture_decorator, ast.Call):
                for kw in fixture_decorator.keywords:
                    if kw.arg == "scope" and isinstance(kw.value, ast.Str):
                        scope = kw.value.s
                    if kw.arg == "autouse" and isinstance(kw.value, ast.Constant):
                        autouse = bool(kw.value.value)
                    if kw.arg == "params" and isinstance(
                        kw.value, (ast.List, ast.Tuple)
                    ):
                        params = [
                            elt.s for elt in kw.value.elts if isinstance(elt, ast.Str)
                        ]
            docstring = ast.get_docstring(node) or ""
            dependencies = [arg.arg for arg in node.args.args]
            self.fixtures[fixture_name] = {
                "name": fixture_name,
                "scope": scope,
                "autouse": autouse,
                "params": params,
                "docstring": docstring,
                "dependencies": dependencies,
                "line_number": node.lineno,
            }
        elif node.name.startswith("test_"):
            # Test function: record parameter names (used fixtures)
            params = [arg.arg for arg in node.args.args]
            self.test_functions[node.name] = {
                "name": node.name,
                "params": params,
                "line_number": node.lineno,
            }
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # Track imported fixtures from conftest or fixtures modules
        if node.module and ("conftest" in node.module or "fixtures" in node.module):
            for alias in node.names:
                self.imported_fixtures.add(alias.name)


class FixtureAuditorAST:
    def __init__(self, tests_dir: str = "backend/tests"):
        self.tests_dir = Path(tests_dir)
        self.fixtures = {}
        self.fixture_usage = defaultdict(set)
        self.test_files = []
        self.analysis_results = {}
        self.imported_fixtures = set()

    def scan_test_files(self) -> List[Path]:
        test_files = []
        for py_file in self.tests_dir.rglob("*.py"):
            if py_file.name.startswith("test_") or py_file.name == "conftest.py":
                test_files.append(py_file)
        return sorted(test_files)

    def extract_fixtures_and_usage(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return {}, {}, set()
        try:
            tree = ast.parse(content, filename=str(file_path))
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return {}, {}, set()
        visitor = FixtureVisitor()
        visitor.visit(tree)
        return visitor.fixtures, visitor.test_functions, visitor.imported_fixtures

    def run_audit(self) -> Dict[str, Any]:
        print("🔍 Starting AST-based fixture audit...")
        self.test_files = self.scan_test_files()
        print(f"📁 Found {len(self.test_files)} test files")
        for file_path in self.test_files:
            (
                file_fixtures,
                test_functions,
                imported_fixtures,
            ) = self.extract_fixtures_and_usage(file_path)
            for fixture_name, info in file_fixtures.items():
                info["file"] = str(file_path)
                self.fixtures[fixture_name] = info
            for test_name, info in test_functions.items():
                for param in info["params"]:
                    self.fixture_usage[param].add(str(file_path))
            self.imported_fixtures.update(imported_fixtures)
        print(f"🔧 Found {len(self.fixtures)} fixtures")
        self.analysis_results = {
            "total_fixtures": len(self.fixtures),
            "total_test_files": len(self.test_files),
            "fixtures_by_category": self.categorize_fixtures(),
            "scope_distribution": self.analyze_scope_distribution(),
            "potential_duplicates": self.find_duplicates(),
            "fixture_details": self.fixtures,
            "usage_mapping": {k: list(v) for k, v in self.fixture_usage.items()},
            "imported_fixtures": list(self.imported_fixtures),
        }
        return self.analysis_results

    def categorize_fixtures(self) -> Dict[str, List[str]]:
        categories = {
            "database": [],
            "authentication": [],
            "application": [],
            "utility": [],
            "test_data": [],
            "mocking": [],
            "performance": [],
            "other": [],
        }
        for fixture_name, fixture_info in self.fixtures.items():
            category = self._categorize_fixture(
                fixture_name, fixture_info["file"], fixture_info.get("docstring", "")
            )
            categories[category].append(fixture_name)
        return categories

    def find_duplicates(self) -> Dict[str, List[str]]:
        duplicates = {}
        fixture_names = list(self.fixtures.keys())
        for i, name1 in enumerate(fixture_names):
            for name2 in fixture_names[i + 1 :]:
                if self._are_similar_fixtures(name1, name2):
                    if name1 not in duplicates:
                        duplicates[name1] = []
                    duplicates[name1].append(name2)
        return duplicates

    def _are_similar_fixtures(self, name1: str, name2: str) -> bool:
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        if name1_lower == name2_lower and name1 != name2:
            return True
        common_patterns = [
            ("test_", ""),
            ("_test", ""),
            ("mock_", ""),
            ("fake_", ""),
            ("stub_", ""),
        ]
        for pattern, replacement in common_patterns:
            clean1 = name1_lower.replace(pattern, replacement)
            clean2 = name2_lower.replace(pattern, replacement)
            if clean1 == clean2 and clean1:
                return True
        return False

    def analyze_scope_distribution(self) -> Dict[str, int]:
        scope_counts = defaultdict(int)
        for fixture_info in self.fixtures.values():
            scope_counts[fixture_info["scope"]] += 1
        return dict(scope_counts)

    def generate_report(self, output_file: str = "fixture_audit_report.json") -> None:
        if not self.analysis_results:
            self.run_audit()
        report = {
            "summary": {
                "total_fixtures": self.analysis_results["total_fixtures"],
                "total_test_files": self.analysis_results["total_test_files"],
                "fixtures_by_category": self.analysis_results["fixtures_by_category"],
                "scope_distribution": self.analysis_results["scope_distribution"],
                "potential_duplicates": self.analysis_results["potential_duplicates"],
                "imported_fixtures": self.analysis_results["imported_fixtures"],
            },
            "fixture_details": self.analysis_results["fixture_details"],
            "usage_mapping": self.analysis_results["usage_mapping"],
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"📊 Report generated: {output_file}")

    def print_summary(self) -> None:
        if not self.analysis_results:
            self.run_audit()
        print("\n" + "=" * 60)
        print("🔍 AST-BASED FIXTURE AUDIT SUMMARY")
        print("=" * 60)
        print(f"📁 Test Files Analyzed: {self.analysis_results['total_test_files']}")
        print(f"🔧 Total Fixtures Found: {self.analysis_results['total_fixtures']}")
        print("\n📊 Fixtures by Category:")
        for category, fixtures in self.analysis_results["fixtures_by_category"].items():
            if fixtures:
                print(f"  {category.capitalize()}: {len(fixtures)} fixtures")
        print("\n🎯 Scope Distribution:")
        for scope, count in self.analysis_results["scope_distribution"].items():
            print(f"  {scope}: {count} fixtures")
        print("\n⚠️  Potential Duplicates:")
        duplicates = self.analysis_results["potential_duplicates"]
        if duplicates:
            for fixture, similar in duplicates.items():
                print(f"  {fixture} -> {', '.join(similar)}")
        else:
            print("  No obvious duplicates found")
        print("\n📈 Most Used Fixtures:")
        usage_counts = [
            (name, len(files))
            for name, files in self.analysis_results["usage_mapping"].items()
        ]
        usage_counts.sort(key=lambda x: x[1], reverse=True)
        for name, count in usage_counts[:10]:
            print(f"  {name}: used in {count} files")
        print("\n📦 Imported Fixtures:")
        for name in self.analysis_results["imported_fixtures"]:
            print(f"  {name}")

    def _categorize_fixture(
        self, fixture_name: str, file_path: str, docstring: str
    ) -> str:
        """Categorize a fixture based on its name, file location, and docstring."""

        # Check if fixture is already centralized in conftest.py
        if file_path == "backend/tests/conftest.py":
            if fixture_name in ["dummy_metrics"]:
                return "test_data"
            elif fixture_name in [
                "anyio_backend",
                "event_loop",
                "freezer",
                "reset_rate_limiter",
            ]:
                return "utility"
            elif fixture_name in ["client"]:
                return "application"
            elif fixture_name in ["sync_session", "patch_sync_db", "override_get_db"]:
                return "database"
            elif fixture_name in ["mock_settings"]:
                return "mocking"

        # Categorize based on name patterns and file location
        name_lower = fixture_name.lower()

        # Database fixtures
        if any(word in name_lower for word in ["db", "session", "database"]):
            return "database"

        # Authentication fixtures
        if any(
            word in name_lower for word in ["auth", "user", "jwt", "token", "login"]
        ):
            return "authentication"

        # Application fixtures
        if any(word in name_lower for word in ["client", "app", "server"]):
            return "application"

        # Utility fixtures
        if any(
            word in name_lower
            for word in ["freezer", "reset", "clear", "isolate", "patch"]
        ):
            return "utility"

        # Test data fixtures
        if any(
            word in name_lower for word in ["sample", "dummy", "test_data", "mock_data"]
        ):
            return "test_data"

        # Mocking fixtures
        if name_lower.startswith("mock_") or "mock" in name_lower:
            return "mocking"

        # Performance fixtures
        if any(
            word in name_lower for word in ["benchmark", "performance", "container"]
        ):
            return "performance"

        # Default to other
        return "other"


def main():
    auditor = FixtureAuditorAST()
    try:
        auditor.run_audit()
        auditor.print_summary()
        auditor.generate_report()
        print("\n✅ AST-based fixture audit completed successfully!")
    except Exception as e:
        print(f"❌ Error during fixture audit: {e}")
        raise


if __name__ == "__main__":
    main()
