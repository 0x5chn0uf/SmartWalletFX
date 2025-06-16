# DeFi Tracker – Testing & QA Guide

> Version 0.1 – drafted 2025-06-16

## 1. Goals & Principles
- **Reliability first**: safeguard critical financial calculations.
- **Shift-left**: catch issues in unit & integration layers before E2E.
- **Fast feedback**: CI runs < 10 min; dev locally < 30 s.
- **Coverage gates**: ≥ 90 % backend, ≥ 75 % frontend.

## 2. Directory Conventions
```
backend/tests/
    unit/
    integration/
    property/
    e2e/
frontend/src/__tests__/
    unit/
    integration/
    e2e/ (Cypress)
```

## 3. Toolchain
| Layer | Tooling |
|-------|---------|
| Backend – Unit | `pytest`, `pytest-asyncio` |
| Backend – Property | `hypothesis` |
| Backend – Performance | `pytest-benchmark` |
| Frontend – Unit | `@testing-library/react`, `jest` |
| Frontend – Storybook snapshots | `@storybook/test-runner` |
| Frontend – Integration | `msw` for API mocks |
| End-to-End | `Cypress` (Chrome / Mobile viewport) |
| Security | `bandit`, `safety`, `detect-secrets` |
| Linting | `ruff`, `mypy`, `eslint`, `prettier` |

## 4. CI Pipeline Stages
1. **security** – bandit, safety, detect-secrets.
2. **quality** – ruff, mypy, eslint.
3. **test** – pytest (`--cov`), jest (`--coverage`).
4. **e2e** – Cypress Docker job.
5. **deploy** – only if all above pass and branch=main.

## 5. Mocking External Dependencies
- **Alchemy / EVM RPC**: mocked via `responses` (`pytest`) and `msw` (frontend).
- **CoinGecko**: cached fixture JSON; use `VCR.py` for integration tests.
- **Redis & Celery**: `fakeredis` and `celery.app.control.inspect` mock.

## 6. Property-Based Testing Examples
```python
from hypothesis import given, strategies as st

@given(total=st.decimals(min_value=0), borrowed=st.decimals(min_value=0))
def test_health_score_range(total, borrowed):
    score = calculate_health_score(total, borrowed)
    assert 0 <= score <= 999
```

## 7. Running Tests Locally
```bash
# backend
poetry run pytest --cov=app --cov-report=term-missing

# frontend
cd frontend && npm test -- --watchAll=false --coverage

# storybook visual regression
npm run test-storybook

# e2e (headed)
cd frontend && npx cypress open
```

## 8. Coverage Badges
Badges are auto-updated by CI in README using `codecov` uploads.

## 9. Performance & Load Testing (Future)
- Use `locust` for backend load profiles.
- Lighthouse-CI for frontend performance budgets. 