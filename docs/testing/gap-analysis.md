# Testing Gap Analysis

> **Status:** Draft – generated 2025-06-15 as part of Subtask 2.7 (Develop Testing & Validation Strategy)

## Purpose
Provide a snapshot of current automated test coverage, identify untested or under-tested areas, and prioritise actions to reach the target coverage thresholds (≥ 90 % backend, ≥ 75 % frontend).

## Methodology
1. Generate baseline coverage reports for backend (`pytest --cov`) and frontend (`npm test -- --coverage`).
2. Parse HTML/XML/lcov outputs to calculate statement, branch, and function coverage.
3. Map uncovered lines/functions to risk categories (critical path, peripheral, experimental).
4. Record performance metrics (pytest-bench, Lighthouse) to correlate with code paths.

## Current Coverage Snapshot *(placeholder – replace after baseline run)*
| Layer | Statements % | Branch % | Functions % | Notes |
|-------|--------------|----------|--------------|-------|
| Backend | 94 | – | – | Report `reports/coverage-backend-2025-06-15.xml` |
| Frontend | 58 | – | – | Report `reports/coverage-frontend-2025-06-15/` |

## Key Gaps Identified *(to be completed)*
- **Backend**
  - [ ] Snapshot aggregation error-paths
  - [ ] Celery task retries & failure handling
- **Frontend**
  - [ ] TimelineChart edge cases (empty data, extreme values)
  - [ ] Responsive navigation interactions on mobile

## Action Items
| # | Gap | Suggested Test | Priority | Owner |
|---|-----|----------------|---------|-------|
| GA-1 | Snapshot service error handling | Property-based tests with Hypothesis | High | Backend Dev |
| GA-2 | TimelineChart extreme values | RTL + Jest visual snapshots | Medium | Frontend Dev |

---
*Document generated automatically. Update after each audit iteration.* 