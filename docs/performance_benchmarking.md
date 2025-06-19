# Performance Benchmarking Guide – Authentication & Security

> **Audience:** Backend engineers, QA engineers, DevOps engineers
>
> **Scope:** Micro-benchmarks (bcrypt, JWT), constant-time variance checks, and macro load testing for the authentication stack.  This guide explains _why_ we measure, _what_ we measure, and _how_ to interpret the results locally and in CI.

---

## 1. Rationale
High-cost cryptographic primitives (bcrypt) and security middleware (JWT validation, constant-time checks) guard every request.  Their latency directly affects user experience and the ability to scale.  Automated performance tests give us:

* Early detection of regressions introduced by library upgrades or code changes.
* A data-driven way to tune bcrypt rounds per environment.
* Historical trends that inform hardware sizing and rate-limit budgets.
* Confidence that constant-time guarantees hold under realistic load.

---

## 2. Toolkit Overview
| Tool | Purpose | Location |
|------|---------|----------|
| **pytest-benchmark** | Micro-benchmarks for Python call-sites (bcrypt hash/verify, JWT encode/decode). Autosaves JSON + histogram. | `backend/tests/performance/*`
| **Security Test Framework (STF)** | Statistical helpers for constant-time assertions (<https://link/to/doc>) | `backend/tests/utils/security_testing.py`
| **Locust** | Macro load testing (HTTP).  Smoke profile in CI; full profile for nightly pipeline. | `backend/locustfile.py`

All dependencies are pinned in `backend/requirements/perf.txt` and installed via `make install-perf` locally or automatically in CI.

---

## 3. Running Benchmarks Locally
```bash
# 1 – activate venv & install perf deps
make install-perf  # installs pytest-benchmark + locust

# 2 – run micro-benchmarks (bcrypt, JWT, constant-time)
pytest --benchmark-only tests/performance | tee perf.txt

# 3 – view detailed report (opens browser)
pytest-benchmark compare --histogram *.json

# 4 – run Locust smoke test (make sure backend is running)
make serve &             # launches uvicorn in the background
make locust-smoke        # 100 users, 30 s duration
```

### 3.1 Environment Variables
| Variable | Default | Meaning |
|----------|---------|---------|
| `BCRYPT_ROUNDS` | `12` (prod), `4` (tests) | Hashing cost factor – lower in CI to keep duration reasonable. |
| `BENCH_VARIANCE_FACTOR` | `0.15` | Allowed relative regression before CI fails (15 %). |
| `STF_VARIANCE_THRESHOLD` | `0.30` | Constant-time tolerance in timing tests (30 %). |

Override them per-shell or in GitHub Actions to tune thresholds.

---

## 4. Interpreting Results
### 4.1 pytest-benchmark Output
* **Mean ± StdDev** – primary latency metric (lower is better).
* **Median** – robust against outliers; used for CI regression comparison.
* **Histogram** – quick visual of distribution skew and tail-latency.

A regression is flagged when the new median exceeds the saved baseline by more than `$BENCH_VARIANCE_FACTOR × 100 %` (default 15 %).

### 4.2 STF Constant-Time Checks
`assert_timing_attack_resistant` compares distributions of *successful* vs *failed* password verifications.  We pass if the relative standard deviation ≤ `STF_VARIANCE_THRESHOLD` (30 % by default).  Failures are rare in CI; investigate noisy runners or cryptographic refactors.

### 4.3 Locust Smoke Report
CI uploads the Locust HTML and stats CSV artifacts.  Key metrics:
* **RPS (Requests/s)** – sustained throughput during the 30 s test.
* **P95 Latency** – should remain ≤ 300 ms.
* **Failures** – must stay at **0**; any non-200 is a hard failure.

---

## 5. CI Integration
The `performance-tests` job in `.github/workflows/ci-cd.yml` executes:
1. `pytest --benchmark-only` – generates `.benchmarks` artefact.
2. Compares against the previous commit's autosaved baseline (if available).
3. Starts the backend (`uvicorn`) and runs the Locust smoke profile (`make locust-smoke`).
4. Uploads artifact bundle: `pytest` JSON, histogram PNGs, and Locust HTML.

The job **fails** when:
* Any micro-benchmark median exceeds baseline by > `BENCH_VARIANCE_FACTOR`.
* STF asserts timing variance > `STF_VARIANCE_THRESHOLD`.
* Locust returns non-zero failures **or** P95 latency > 300 ms.

---

## 6. Threshold Tuning
* Use the first successful CI run on `main` as the **baseline** – its autosaved JSON is stored in the workflow artifacts.
* If intentional changes improve performance, regenerate the baseline:
  ```bash
  pytest --benchmark-only --benchmark-save=baseline-v<new>
  ```
  Commit the new `baseline-<new>.json` to `tests/performance/benchmarks/` (small file) and push.
* If a legitimate regression cannot be fixed immediately, bump `BENCH_VARIANCE_FACTOR` temporarily and create a follow-up task.

---

## 7. Nightly & On-Demand Load Profiles (Future Work)
The current CI smoke test validates basic scalability.  A **full-scale** Locust profile (1 000 users, 10 m test) will run in the scheduled nightly pipeline.  Results feed into Grafana dashboards for trend analysis.  Task 4.15.x will integrate that pipeline.

---

## 8. FAQ & Troubleshooting
| Symptom | Possible Cause | Resolution |
|---------|----------------|------------|
| CI job fails with `BenchmarkMedianRegressed` | Code path added extra DB query or lowered bcrypt rounds in prod vs test | Inspect flamegraph, profile `bcrypt.raise_invalid_rounds`, adjust code, or raise threshold if expected. |
| STF constant-time test flaky on PRs | GitHub runner jitter | Increase `STF_VARIANCE_THRESHOLD` to `0.40` for that run, retry, then investigate root cause. |
| Locust smoke cannot authenticate (`401`) | Test user missing or password mismatch | Ensure `on_start` hook in `locustfile.py` successfully registers the user; check backend logs. |

---

## 9. References
* [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
* [Locust Documentation](https://docs.locust.io/)
* [OWASP Cheat Sheet – Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
* [Timing Attack Mitigation Techniques](https://crypto.stanford.edu/
benign/gadelrab23_timing.pdf)

---

*Last Updated: 2025-06-19* 