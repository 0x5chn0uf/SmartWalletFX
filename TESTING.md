# SmartWalletFX – Backend Testing Guide

> **Purpose**: Describe how we test the FastAPI backend.

---

## 1  Testing Philosophy

We ship only when **all tests are green** and lint passes.  Tests mirror the hexagonal architecture:

| Scope           | Goal                                       | Boundaries                                              |
| --------------- | ------------------------------------------ | ------------------------------------------------------- |
| **Unit**        | Validate isolated business rules & helpers | No I/O – repositories + services mocked via DIContainer |
| **Integration** | Ensure components collaborate correctly    | Postgres + Redis launched in Docker; Web3 calls faked   |
| **Performance** | Detect regressions on hot paths            | Marked `@pytest.mark.performance`, run nightly          |

Coverage gate: **≥ 90 % lines / 80 % branches**.

---

## 2  Directory Layout

```
backend/
└── tests/
    ├── unit/           # Fast, pure‑python
    ├── integration/    # Container‑backed
    ├── performance/    # Benchmarks
    └── fixtures/       # Shared pytest fixtures
```

*Fixtures are grouped by concern* (`auth.py`, `di_container.py`, `web3.py`, …).

---

## 3  Running the Suite

### 3.1 Primary targets

| Purpose                                | Command                                                                  |
| -------------------------------------- | ------------------------------------------------------------------------ |
| **Quiet run (Claude, CI diff checks)** | `make test-quiet` *(maps to* `pytest -q --tb=short --color=no tests/`*)* |
| **Full suite**                         | `make test`                                                              |
| **With coverage**                      | `make test-cov`                                                          |
| **Performance only**                   | `make test-perf`                                                         |
| **Single dir**                         | `pytest tests/unit/`                                                     |
| **Single test**                        | `pytest -k "test_name"`                                                  |

### 3.2 Useful options

```bash
pytest -q                  # minimal noise
pytest -x                  # stop after first failure
pytest --maxfail=5         # cap failures
pytest -m "not performance" # skip heavy perf tests
```

---

## 4  Fixtures & Dependency Injection

* **DI‑aware**: Tests obtain collaborators via `di_container` fixture to avoid real singletons.
* **Async**: Most fixtures are `async def`; pytest‑asyncio configured in `conftest.py`.
* **Database**: A fresh Postgres container is started per integration session; rolled back between tests.
* **Redis**: Ephemeral container using unique DB index per worker.
* **Web3**: `FakeWeb3` stub injects canned chain data; no external RPC calls.

Example unit fixture pattern:

```python
@pytest.fixture
def wallet_usecase(mock_wallet_repo, mock_user_repo, mock_config, mock_audit):
    return WalletUsecase(mock_wallet_repo, mock_user_repo, mock_config, mock_audit)
```

---

## 5  Markers & Selectors

| Marker                     | Meaning                                        |
| -------------------------- | ---------------------------------------------- |
| `@pytest.mark.integration` | Requires Postgres/Redis containers             |
| `@pytest.mark.performance` | Benchmarks > 500 ms, excluded from default run |
| `@pytest.mark.web3`        | Tests touching blockchain logic                |

Add new markers in `pytest.ini`.

---

## 6  Continuous Integration

* GitHub Actions workflow `ci.yml` runs: `make lint`, `make test-quiet`, coverage upload.
* Fail‑fast if coverage gate not met.
* Docker services spawned via `services:` matrix.

---

## 7  Recommended Workflow

1. **Red ➜ Green**: write failing test, implement code, make it pass.
2. **Run Locally**: `make test-quiet` before each commit.
3. **Format & lint**: `make format && make lint`.
4. **Push / CI**: rely on GitHub Actions to repeat the suite.

---

## 8  Debugging Failing Tests

* Re‑run last failures: `pytest --lf -vv`.
* Drop into pdb: `pytest tests/… -k name -x --pdb`.
* Show locals in tracebacks: `pytest -vv --showlocals`.
* Capture logs: `pytest -s` (disable stdout capture).

---

## 9  Adding New Tests

* Place in the same layer directory (`unit/`, `integration/` …).
* Name file `test_<subject>.py`; name function `test_<expected_behavior>`.
* Prefer *Arrange‑Act‑Assert* structure.
* Use `freezegun` for time travel, `pytest-mock` for patches.

---

## 10  Cheat‑Sheet

| Need to…                    | Command                                      |
| --------------------------- | -------------------------------------------- |
| Re‑run just‑failed tests    | `pytest --lf`                                |
| Run with coverage report    | `pytest --cov=app --cov-report=term-missing` |
| Show 10 slowest tests       | `pytest --durations=10`                      |
| Generate JUnit XML for IDEs | `pytest --junitxml=report.xml`               |

---

*Last updated : 17 July 2025*
