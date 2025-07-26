# BACKEND_WORKFLOW.md

> **Audience**: Claude Code when working on Python/FastAPI backend code
> **Scope**: All tasks involving `backend/` directory, Python files, API routes, database models

---

## Essential Setup

### 🚨 PREREQUISITE: Virtual Environment

**Before running ANY command in this workflow**, ensure you are in the backend directory with the virtual environment activated:

```bash
cd backend && source .venv/bin/activate
```

This command is safe to run multiple times and should be your first step for any backend work.

**All commands below assume you have already done this setup step.**

### Verify Environment

```bash
which python  # Should point to .venv/bin/python
pip list      # Check installed packages
```

---

## Testing Workflow

### 🎯 Primary Test Command (TOKEN-EFFICIENT - use this by default)

```bash
make test-quiet
```

**⚠️ IMPORTANT**: Always use `make test-quiet` to minimize token usage. This provides essential test results without verbose output that consumes tokens unnecessarily.

### 🔍 Single Test Debugging (TOKEN-EFFICIENT)

When working on specific failing tests, target exactly what you need:

```bash
# By pattern/expression (most efficient for specific tests)
pytest -q --tb=short --color=no -k "test_wallet"

# By exact test node (pinpoint testing)
pytest -q --tb=short --color=no tests/test_wallets.py::TestWalletService::test_create_wallet

# Specific test file only
pytest -q --tb=short --color=no tests/test_wallets.py
```

### Additional Token-Saving Options

```bash
# Even more minimal output
pytest -q --tb=no --no-header tests/

# Fail fast (stop on first failure)
pytest -q --tb=short --color=no -x tests/

# Show only failures
pytest -q --tb=short --color=no --lf tests/
```

### 📊 Verbose Output (ONLY when debugging specific issues)

```bash
make test        # Full verbose output - AVOID unless necessary
pytest -v tests/ # Alternative verbose - AVOID unless necessary
```

**🚨 WARNING**: Verbose test output consumes significant tokens. Only use when you need detailed debugging information for specific test failures.

### Coverage Reports

```bash
make test-cov
```

---

## Code Quality & Linting

### Before Every Commit

```bash
make lint        # Run all linting checks
make format      # Auto-format code
```

### Individual Commands

```bash
make bandit      # Security scanning
make safety      # Dependency vulnerability check
black .          # Code formatting
isort .          # Import sorting
flake8 .         # Style checking
mypy .           # Type checking
```

---

## Development Server

### Start Local FastAPI Server

```bash
make run         # Starts uvicorn development server
```

### Database & Services

```bash
make db-start    # Start PostgreSQL & Redis containers
make db-stop     # Stop containers
make db-reset    # Reset database schema
```

---

## Common Backend Tasks

### API Development

1. **Create new endpoint**: Add route in appropriate module
2. **Test first**: Write test in `tests/` matching file structure
3. **Implement**: Code the endpoint logic
4. **Validate**: Run `make test-quiet` and fix any failures
5. **Document**: Update API docs if needed

### Database Changes

1. **Migration**: Create Alembic migration if schema changes
2. **Test**: Ensure all database tests pass
3. **Seed data**: Update fixtures if needed

### Service Layer Changes

1. **Unit tests**: Test business logic in isolation
2. **Integration tests**: Test with database/external services
3. **Error handling**: Ensure proper exception handling

---

## Debugging Patterns

### Failed Tests

```bash
# Run only failing test with more context
pytest -vvs tests/path/to/test_file.py::test_name

# Debug with pdb
pytest --pdb tests/path/to/test_file.py::test_name
```

### API Issues

```bash
# Check server logs
make run  # Watch terminal output

# Test endpoints manually
curl -X GET http://localhost:8000/api/health
```

### Database Issues

```bash
# Check database connection
make db-status

# Run database tests only
pytest tests/test_database/ -v
```

---

## Handy Make Targets Reference

| Purpose                   | Command            |
| ------------------------- | ------------------ |
| Install dev dependencies  | `make install-dev` |
| **Primary test suite**    | `make test-quiet`  |
| Full test suite (verbose) | `make test`        |
| Coverage report           | `make test-cov`    |
| **Lint & format**         | `make lint`        |
| **Auto-format code**      | `make format`      |
| Security scans            | `make bandit`      |
| Dependency security       | `make safety`      |
| **Start dev server**      | `make run`         |
| Start database containers | `make db-start`    |
| Stop database containers  | `make db-stop`     |

---

## Completion Checklist

Before marking any backend task complete:

- [ ] Virtual environment activated: `cd backend && source .venv/bin/activate`
- [ ] **All tests passing (TOKEN-EFFICIENT)**: `make test-quiet`
- [ ] Code properly formatted: `make format`
- [ ] Linting passes: `make lint`
- [ ] No security issues: `make bandit`
- [ ] Changes committed with conventional commit message
- [ ] Task Master updated: mark task as done
- [ ] Memory Bank updated:
  - Archive created: `.taskmaster/memory-bank/archive/archive-<task-id>.md`
  - Reflection created: `.taskmaster/memory-bank/reflection/reflection-<task-id>.md`
  - Progress & activeContext updated

**🎯 TOKEN EFFICIENCY REMINDER**: Always use `make test-quiet` instead of `make test` to conserve tokens during development.

```

---

_Backend workflow - Last updated: 20 July 2025_
```
