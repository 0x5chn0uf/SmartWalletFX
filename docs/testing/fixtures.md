# Backend Test Fixture Audit

_Last updated: 2025-06-24_

## Overview
This document catalogs all pytest fixtures in the backend test suite, maps their usage, and provides recommendations for centralization and deduplication. It is based on an automated AST-based audit of the codebase.

**Purpose:**
- Ensure all fixtures are discoverable and documented
- Identify opportunities for centralization and deduplication
- Support maintainable, high-quality testing infrastructure

---

## Fixture Categories

| Category        | Fixtures (Count) |
|----------------|------------------|
| Database       | 5                |
| Authentication | 2                |
| Application    | 1                |
| Utility        | 2                |
| Test Data      | 2                |
| Mocking        | 11               |
| Performance    | 1                |
| Other          | 20               |

---

## Fixture Inventory

| Name | Scope | File | Description | Dependencies |
|------|-------|------|-------------|--------------|
| client | function | backend/tests/conftest.py | FastAPI test client | - |
| sync_session | module | backend/tests/conftest.py | Create a synchronous, in-memory SQLite database session. | - |
| patch_sync_db | module | backend/tests/conftest.py | Patches the sync db engine and session for Celery tasks. | - |
| mock_settings | function | backend/tests/conftest.py | Mocks the ARBITRUM_RPC_URL setting. | monkeypatch |
| dummy_metrics | function | backend/tests/conftest.py | Returns a dummy PortfolioMetrics object. | - |
| override_get_db | function | backend/tests/conftest.py | Fixture to override the 'get_db' dependency in the FastAPI app. | db_session |
| anyio_backend | session | backend/tests/conftest.py | Force AnyIO to use only the asyncio backend during tests. | - |
| freezer | function | backend/tests/conftest.py | Fixture that provides a context manager for freezing time. | - |
| reset_rate_limiter | function | backend/tests/conftest.py | Clear the in-memory rate limiter's storage between tests. | - |
| event_loop | session | backend/tests/conftest.py | Create a dedicated asyncio loop for the entire test session. | - |
| postgres_large_container | module | backend/tests/e2e/test_performance.py | Spins up the postgres-large container (port 5435), yields DB URL, and tears down after tests. | - |
| sample_jwks | function | backend/tests/unit/utils/test_jwks_cache.py | Create a sample JWKSet for testing. | - |
| user_payload | function | backend/tests/integration/auth/test_auth_flow.py | User payload for authentication tests | - |
| _isolate_settings | function | backend/tests/integration/jwt_rotation/test_rotation_task.py | Snapshot & restore mutable settings between tests. | monkeypatch |
| _patch_redis_and_lock | function | backend/tests/integration/jwt_rotation/test_rotation_task.py | Patch Redis client builder and *acquire_lock* helper for isolation. | monkeypatch |
| mock_redis | function | backend/tests/unit/utils/test_metrics_cache.py | Mock Redis client. | self |
| patched_auth_service | function | backend/tests/integration/test_auth.py | Patch *AuthService* used in auth endpoints with DummyAuthService. | monkeypatch |
| _reset_rate_limiter | function | backend/tests/integration/test_auth.py | Ensure in-memory rate-limiter is cleared between tests in this module. | - |
| mock_w3 | function | backend/tests/integration/test_defi_aave_endpoint.py | Mock Web3 instance for Aave tests | - |
| dummy_redis | function | backend/tests/integration/test_defi_aggregate_endpoint.py | Dummy Redis instance for testing | monkeypatch |
| mock_w3_compound | function | backend/tests/integration/test_defi_compound_endpoint.py | Mock Web3 instance for Compound tests | - |
| _dependency_override | function | backend/tests/integration/test_timeline_dynamic_aggregator_endpoints.py | Override database dependency for timeline tests | db_session |
| adapter | function | backend/tests/unit/adapters/test_radiant_contract_adapter.py | Return a RadiantContractAdapter instance with on-chain calls mocked. | monkeypatch, tmp_path |
| _clean_state | function | backend/tests/unit/auth/test_jwt_rotation.py | Ensure we start each test with a clean key-set state. | monkeypatch |
| mock_output_dir | function | backend/tests/unit/backups/test_audit_logging.py | Provides a temporary directory for backup dumps. | tmp_path |
| tmp_output_dir | module | backend/tests/unit/backups/test_backup_cmd.py | Temporary output directory for backup tests | tmp_path_factory |
| _clear_w3_cache | function | backend/tests/unit/core/test_dependencies.py | Ensure the Web3 provider cache is cleared before & after each test. | - |
| mock_db | function | backend/tests/unit/services/test_defi_aggregation_service.py | Mock database session. | self |
| repo | function | backend/tests/unit/repositories/test_aggregate_metrics_repository.py | Mock repository instance | mock_db |
| sample_model | function | backend/tests/unit/repositories/test_aggregate_metrics_repository.py | Sample model for testing | - |
| blockchain_service | function | backend/tests/unit/services/test_blockchain_service.py | Blockchain service instance. | self |
| mock_web3 | function | backend/tests/unit/services/test_blockchain_service.py | Mock Web3 instance. | self |
| data_analysis_service | function | backend/tests/unit/services/test_data_analysis_service.py | Create a DataAnalysisService instance for testing. | self, db_session |
| mock_portfolio_metrics | function | backend/tests/unit/services/test_data_analysis_service.py | Mock portfolio metrics. | self |
| mock_metrics_repo | function | backend/tests/unit/services/test_defi_aggregation_service.py | Mock aggregate metrics repository. | self |
| mock_position_adapter | function | backend/tests/unit/services/test_defi_aggregation_service.py | Mock DeFi position adapter. | self |
| aggregation_service | function | backend/tests/unit/services/test_defi_aggregation_service.py | DeFi aggregation service instance. | self, mock_db, mock_redis |
| sample_positions | function | backend/tests/unit/services/test_defi_aggregation_service.py | Sample DeFi positions for testing. | self |
| sample_metrics_model | function | backend/tests/unit/services/test_defi_aggregation_service.py | Sample AggregateMetricsModel instance. | self |
| mock_db_session | function | backend/tests/unit/services/test_portfolio_service.py | Mock database session. | self |
| portfolio_service | function | backend/tests/unit/services/test_portfolio_service.py | Portfolio calculation service instance. | self, mock_db_session |
| mock_snapshot_data | function | backend/tests/unit/services/test_portfolio_service.py | Mock portfolio snapshot data. | self |
| sample_metrics_data | function | backend/tests/unit/utils/test_metrics_cache.py | Sample metrics data for testing. | self |
| sample_metrics_schema | function | backend/tests/unit/utils/test_metrics_cache.py | Sample AggregateMetricsSchema instance. | sample_metrics_data |

---

## Usage Mapping

**Most Used Fixtures:**

| Fixture Name | Used In (Test Files) |
|--------------|----------------------|
| monkeypatch | 20 files |
| self | 14 files |
| tmp_path | 11 files |
| client | 6 files |
| mock_settings | 4 files |
| benchmark | 2 files |
| pwd | 2 files |
| adapter | 2 files |
| mock_web3 | 2 files |
| mock_audit | 2 files |

**Full Usage Mapping:**
- See `fixture_audit_report.json` for a complete mapping of which test modules use which fixtures.

---

## Potential Duplicates & Issues

- No obvious duplicates were found in the latest audit.
- 20 fixtures are uncategorized ("Other"); these should be reviewed for possible centralization or renaming.
- Several fixtures have similar purposes but different names (e.g., `mock_db`, `mock_db_session`, `sync_session`).

---

## Recommendations & Next Steps

1. **Centralize Common Fixtures:**
   - Move frequently used or generic fixtures to `conftest.py`.
   - Standardize naming and scope for clarity.
2. **Review "Other" Fixtures:**
   - Manually inspect uncategorized fixtures for duplication or inconsistent patterns.
   - Refactor or merge as appropriate.
3. **Document All Fixtures:**
   - Ensure every fixture has a clear docstring/description.
   - Update this document as fixtures are refactored or moved.
4. **Integrate Audit in CI:**
   - Add a CI job to run the audit and fail on new duplicates or scope issues.

---

## Appendix
- **Audit Tool:** See `scripts/fixture_audit.py` for the audit script.
- **Full Report:** See `fixture_audit_report.json` for the complete, machine-readable audit output. 