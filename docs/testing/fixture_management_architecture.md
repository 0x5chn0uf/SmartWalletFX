# Fixture Management Tool Architecture

This document describes the implemented architecture of the automated fixture management system located in `/backend/tools/fixture_lint/`.

## Current Implementation Status

✅ **FULLY IMPLEMENTED** - All phases completed and integrated into the development workflow.

## Module Structure

The fixture management tool is implemented as a Python package with the following modules:

### Core Modules

- **`parser.py`** – AST-based static analysis using LibCST to extract pytest fixtures and their dependencies
- **`duplication.py`** – SHA1-based duplicate detection comparing fixture body content
- **`refactor.py`** – LibCST transformer for automated fixture deduplication and import injection
- **`report.py`** – JSON serialization for CI integration and metrics tracking
- **`cli.py`** – Typer-based command line interface with multiple commands

### Data Models

**`FixtureDefinition`** (dataclass):

- `name: str` - Fixture function name
- `path: str` - Absolute file path
- `line: int` - Line number where fixture is defined
- `dependencies: List[str]` - Parameter names (fixture dependencies)
- `body: str` - Complete fixture source code

**`DuplicateGroup`** (dataclass):

- `body_hash: str` - SHA1 hash of fixture body
- `fixtures: List[FixtureDefinition]` - All fixtures with identical bodies

## Data Flow

1. **File Discovery**: CLI recursively finds `test_*.py` files using `Path.rglob()`
2. **Parsing**: LibCST parses each file, extracting fixture decorators and function definitions
3. **Dependency Analysis**: Function parameters are extracted as fixture dependencies
4. **Duplicate Detection**: SHA1 hashing identifies fixtures with identical implementations
5. **Refactoring**: CST transformations remove duplicates and inject canonical imports
6. **Centralization**: Deduplicated fixtures are moved to `tests/fixtures/deduplicated.py`
7. **Reporting**: JSON metrics written to `.fixture_lint_metrics.json`

## CLI Commands

### `analyze [path]`

- Generates complete JSON report of all fixtures and duplicates
- Writes metrics to `.fixture_lint_metrics.json`
- Used for detailed analysis and debugging

### `check [path] [--json]`

- Validates codebase for duplicate fixtures
- Exits with code 1 if duplicates found (CI integration)
- Optional JSON output for programmatic processing

### `deduplicate [path] [--apply]`

- Dry-run mode shows proposed refactoring changes
- `--apply` flag executes the deduplication process
- Preserves import dependencies from original fixtures

### `fix [path]`

- Production command that applies deduplication automatically
- Writes metrics for monitoring trends over time
- Used in automated workflows

## Integration Points

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: fixture-lint
      name: fixture-lint check
      entry: bash -c "cd backend && python3 -m tools.fixture_lint.cli check tests"
      language: system
      pass_filenames: false
      stages: [commit]
```

### CI Pipeline

```yaml
# .github/workflows/ci-cd.yml
fixture-lint:
  name: Fixture Lint
  runs-on: ubuntu-latest
  steps:
    - name: Run fixture-lint
      run: fixture-lint check
```

### Package Installation

```toml
# pyproject.toml
[project.scripts]
fixture-lint = "tools.fixture_lint.cli:app"
```

## Refactoring Engine Details

The refactoring engine uses LibCST to perform safe AST transformations:

1. **Canonical Selection**: Chooses fixture with lexicographically first file path
2. **Import Extraction**: Preserves all imports from canonical fixture
3. **Import Injection**: Adds `from tests.fixtures.deduplicated import <fixture_name>`
4. **Code Removal**: Removes duplicate fixture definitions using `RemovalSentinel`
5. **Module Path Resolution**: Converts file paths to Python module notation

### Deduplication Process

1. Original fixtures in multiple files:

   ```python
   # tests/auth/test_login.py
   @pytest.fixture
   def user():
       return User(email="test@example.com")

   # tests/profile/test_update.py
   @pytest.fixture
   def user():
       return User(email="test@example.com")
   ```

2. After deduplication:

   ```python
   # tests/fixtures/deduplicated.py
   @pytest.fixture
   def user():
       return User(email="test@example.com")

   # tests/auth/test_login.py
   from tests.fixtures.deduplicated import user

   # tests/profile/test_update.py
   from tests.fixtures.deduplicated import user
   ```

## Test Coverage

Comprehensive test suite located in `/backend/tests/infrastructure/fixture_lint/unit/`:

- **`test_parser.py`** - AST parsing and fixture extraction
- **`test_duplication.py`** - SHA1-based duplicate detection
- **`test_refactor.py`** - CST transformation and import injection
- **`test_cli.py`** - Command line interface and file I/O operations

## Metrics and Monitoring

The tool generates `.fixture_lint_metrics.json` with tracking data:

```json
{
  "total_fixtures": 45,
  "duplicate_fixtures": 8,
  "duplicate_groups": 3
}
```

This enables monitoring fixture health over time and measuring the impact of deduplication efforts.
