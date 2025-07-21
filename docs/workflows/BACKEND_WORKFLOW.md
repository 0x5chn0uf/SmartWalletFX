# BACKEND_WORKFLOW.md

> **Audience**: Claude Code when working on Python/FastAPI backend code
> **Scope**: All tasks involving `backend/` directory, Python files, API routes, database models

---

## Essential Setup

### 1. Activate Virtual Environment

**ALWAYS run this first** before any backend task:

```bash
cd backend
source .venv/bin/activate
```

### 2. Verify Environment

```bash
which python  # Should point to .venv/bin/python
pip list      # Check installed packages
```

---

## Testing Workflow

### Primary Test Command (use this by default)

```bash
make test-quiet  # pytest -q --tb=short --color=no tests/
```

### Single Test Debugging

When working on specific failing tests:

```bash
# By pattern/expression
pytest -q --tb=short --color=no -k "test_wallet"

# By exact test node
pytest -q --tb=short --color=no tests/test_wallets.py::TestWalletService::test_create_wallet

# Specific test file
pytest -q --tb=short --color=no tests/test_wallets.py
```

### Verbose Output (only when explicitly requested)

```bash
make test        # Full verbose output
pytest -v tests/ # Alternative verbose
```

### Coverage Reports

```bash
make test-cov    # Generate coverage report
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

- [ ] Virtual environment activated
- [ ] All tests passing: `make test-quiet`
- [ ] Code properly formatted: `make format`
- [ ] Linting passes: `make lint`
- [ ] No security issues: `make bandit`
- [ ] Changes committed with conventional commit message
- [ ] GTD files updated with progress

---

_Backend workflow - Last updated: 20 July 2025_
