# Fixture Monitoring

The fixture_lint tool provides comprehensive monitoring capabilities to track fixture health and duplication across the test suite.

## Metrics Generation

The tool generates metrics in two scenarios:

- When running `fixture-lint analyze <path>` - generates full analysis report + metrics file
- When running `fixture-lint fix <path>` - applies deduplication and updates metrics file

### Metrics File Format

The tool writes `.fixture_lint_metrics.json` containing essential statistics:

```json
{
  "total_fixtures": 4,
  "duplicate_fixtures": 2,
  "duplicate_groups": 1
}
```

**Field Definitions:**

- `total_fixtures` – total number of fixture definitions discovered across all test files
- `duplicate_fixtures` – total fixtures that have identical body content (including whitespace)
- `duplicate_groups` – number of distinct groups of duplicated fixtures

## Analysis Report Structure

The `analyze` command outputs a comprehensive JSON report to stdout:

```json
{
  "fixtures": [
    {
      "name": "sample_fixture",
      "path": "/path/to/test_file.py",
      "line": 5,
      "dependencies": [],
      "body": "\n@pytest.fixture\ndef sample_fixture():\n    return {'key': 'value'}\n    \n"
    }
  ],
  "duplicates": [
    {
      "hash": "17f95396ed033e3ca887a8879aaabaaa03de309b",
      "fixtures": [
        {
          "name": "sample_fixture",
          "path": "/path/to/test_a.py",
          "line": 5,
          "dependencies": [],
          "body": "fixture_body_content"
        },
        {
          "name": "sample_fixture",
          "path": "/path/to/test_b.py",
          "line": 5,
          "dependencies": [],
          "body": "fixture_body_content"
        }
      ]
    }
  ]
}
```

## Duplication Detection

Fixtures are considered duplicates when they have:

- Identical body content (SHA1 hash comparison)
- Same parameter signatures (`dependencies` field)
- Exact whitespace matching

The tool groups duplicates by body hash and tracks:

- Hash of the fixture body content
- All fixtures sharing that hash
- File locations and line numbers

## Current CI Integration Status

**Not Currently Integrated** - The fixture_lint tool exists as a standalone CLI tool:

- Available as `fixture-lint` command via pyproject.toml entry point
- Located in `backend/tools/fixture_lint/`
- No current Makefile integration
- No GitHub Actions or CI pipeline usage
- Manual execution only

## Usage Examples

### Local Development

```bash
# Analyze test suite for duplicates
fixture-lint analyze tests/

# Check for duplicates (exits with code 1 if found)
fixture-lint check tests/

# Preview deduplication changes
fixture-lint deduplicate tests/

# Apply deduplication and update metrics
fixture-lint fix tests/
```

### Example Output

When duplicates are found, the check command shows:

```
duplicate hash 17f95396ed033e3ca887a8879aaabaaa03de309b:
  /path/to/test_a.py:5 sample_fixture
  /path/to/test_b.py:5 sample_fixture
```

## Potential CI Integration

To integrate with CI workflows, consider:

1. **Pre-commit Hook**: Run `fixture-lint check tests/` to prevent duplicate commits
2. **CI Metrics Tracking**: Store `.fixture_lint_metrics.json` as build artifacts
3. **Quality Gates**: Fail builds when `duplicate_groups > 0`
4. **Trend Monitoring**: Track metrics over time to measure fixture health

## Tool Architecture

- **Parser**: Uses LibCST to parse Python AST and extract fixture definitions
- **Duplication**: SHA1 hashing of fixture body content for comparison
- **Refactoring**: Automated import-based deduplication to shared fixtures
- **Reporting**: JSON output for both human and machine consumption
