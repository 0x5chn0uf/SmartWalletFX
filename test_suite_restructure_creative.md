🎨🎨🎨 ENTERING CREATIVE PHASE: Test-Suite Restructure – Fixture & Migration Design

## Component 1: Fixture Architecture

### Requirements & Constraints
- ≤ 20 core fixtures
- Fast collection & load times
- DI-friendly (constructor injection)
- Extensible per domain without cross-coupling
- Keep DB/app/client setup DRY

### Options
| # | Approach | Pros | Cons |
|---|----------|------|------|
|1|Monolithic `core.py`|Simplest import path|Large file, domain coupling, slower discovery|
|2|`core.py` + `domain_fixtures/` sub-packages **(Recommended)**|Clear ownership, lazy domain imports, fast discovery|Slight boilerplate (`conftest` imports)|
|3|Pytest plugin per domain|Highly modular, optional enable/disable|Extra indirection, plugin naming overhead|

### Recommended Approach – Option 2
- `shared/fixtures/core.py` → DB, FastAPI app, http_client, settings
- `shared/fixtures/users.py` → `test_user`, `test_user_with_wallet`
- `shared/fixtures/domain_fixtures/<domain>.py` → domain-specific mocks/builders
- Top-level `tests/conftest.py` imports `core` & `users`; each domain’s `conftest.py` imports its fixture module.

**Verification Checkpoint**: `pytest -q` collection < 1 s, no cross-domain imports.

---

## Component 2: Migration Strategy

### Requirements & Constraints
- No broken CI during transition
- Minimal merge conflicts, reversible steps

### Options
| # | Strategy | Pros | Cons |
|---|----------|------|------|
|A|Single big-bang PR|One review cycle|Huge diff, high risk, CI outage|
|B|Domain-by-domain branches **(Recommended)**|Isolated diffs, easier review, tests green each merge|Requires coordination, 3-5 PRs|
|C|Old & new side-by-side|Zero downtime|Duplicate maintenance, slower tests|

### Recommended Approach – Option B
1. Helper: `invoke migrate_tests --domain <name>` (moves files, rewrites imports).
2. For each domain branch:
   - Run script → fix imports → ensure CI green.
   - Squash-merge → tag milestone.
3. After all domains: remove legacy paths & deprecation notices.

**Verification**: CI green per branch; coverage unchanged.

---

## Component 3: Directory Structure

### Requirements & Constraints
- Intuitive paths aligned with DDD
- Fast grep & collection

### Options
| # | Layout | Pros | Cons |
|---|--------|------|------|
|i|Strict domain root (`tests/auth/unit`, …)|Short paths|Infra tests harder to place|
|ii|Domain **plus** infrastructure (PRD sketch) **(Recommended)**|Clear domain vs infra, mirrors code|Slightly deeper tree|
|iii|Gradual addition alongside current|Least disruption|Two conventions coexist long-term|

### Recommended Layout – Option ii
```
backend/tests/
├── domains/<domain>/{unit,integration,e2e}
├── infrastructure/<topic>/
├── shared/{fixtures,strategies,utils}/
└── performance/
```

**Verification**: `pytest tests/domains/auth/unit` runs only Auth unit tests.

---

🎨🎨🎨 EXITING CREATIVE PHASE

All design decisions recorded. Next step: **IMPLEMENT MODE** – execute phased migration and fixture creation. 