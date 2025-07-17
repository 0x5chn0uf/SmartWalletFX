# Test-Suite Migration Instructions

> Follow these steps **exactly** to finish Phase-6 test-suite restructure.
>
> All commands are run from **project root** (`trading_bot_smc`).

---

## 0 . Preconditions
```bash
python --version      # should be 3.10+
git status            # working tree must be clean
```

---

## 1 . Extend the helper script
Edit `backend/tools/migrate_tests.py` → extend `MAPPING_RULES` with rules for *all* remaining areas.

| key | legacy folders (`backend/tests/...`) | new folder |
|-----|--------------------------------------|------------|
| `admin`   | `unit/api` admin tests  <br>`integration/admin` | `domains/admin/{unit,integration}` |
| `defi`    | `unit/strategies`  <br>`integration/defi` | `domains/defi/{unit,integration}` |
| `jwt_rotation` | `unit/jwt_rotation`  <br>`integration/jwt_rotation`  <br>`property/jwt_rotation` | `domains/auth/{unit,integration,property}` |
| `repositories` | `unit/repositories` | `infrastructure/database/unit` |
| `usecase` | `unit/usecase` | `domains/shared/unit` |
| `core` | `unit/core`  <br>`integration/core` | `infrastructure/core/{unit,integration}` |
| `monitoring` | `unit/monitoring`  <br>`integration/monitoring` | `infrastructure/monitoring/{unit,integration}` |
| `utils` | `unit/utils` | `infrastructure/utils/unit` |
| `validators` | `unit/validators` | `infrastructure/security/unit` |

*(Add more rules if stray tests appear.)*

---

## 2 . Migrate per domain
For every **key** above run:
```bash
python -m backend.tools.migrate_tests --domain <key>          # dry-run preview
python -m backend.tools.migrate_tests --domain <key> --apply  # perform moves
pytest backend/tests/<new_path_prefix>/<key>/ -q              # quick check
```
Repeat until legacy `unit/`, `integration/`, `property/` dirs contain **no** test_*.py files.

---

## 3 . Clean up empty legacy dirs
```bash
find backend/tests/unit -type f -name 'test_*.py'      # should output nothing
find backend/tests/integration -type f -name 'test_*.py'
rm -rf backend/tests/unit backend/tests/integration backend/tests/property
```

---

## 4 . Full test-suite
```bash
cd backend
pytest -q
```
All tests must pass.

---

## 5 . Update docs & tasks
* Tick remaining Phase-6 boxes in `tasks.md`.
* Add a short completion note to `backend/PHASE6_SUMMARY.md`.

---

## 6 . Commit
```bash
git add backend/tests backend/tools/migrate_tests.py tasks.md backend/PHASE6_SUMMARY.md
git commit -m "fix(test): complete test-suite domain migration"
```

---

## 7 . Final verification
```bash
pytest -q                    # assurance
git status                   # working tree clean
```

**Phase-6 migration finished.** 