# Test Suite Restructure Implementation Plan

## Overview
This plan addresses the comprehensive restructuring of the backend test-suite to align with modern architecture patterns while completing Phase 6 of the DI refactoring. The task is Level 4 (Complex System) requiring architectural-level changes across 300+ test files.

## Complexity Assessment
**Level 4 - Complex System**
- Scope: 300+ test files across entire backend test-suite
- Architecture impact: Complete domain reorganization + DI pattern migration
- Dependencies: Must align with Phase 6 DI refactoring completion
- Risk: High (large-scale file moves, potential merge conflicts)

## Technology Stack
- **Framework**: pytest (existing)
- **Fixture System**: pytest fixtures with domain-specific organization
- **DI Pattern**: Constructor injection with mock dependencies
- **Coverage**: pytest-cov (maintain ≥47% baseline)

## Technology Validation Checkpoints
- [x] pytest framework validated and working
- [x] Current test structure documented
- [x] DI pattern examples established (test_*_di.py files)
- [x] Fixture architecture defined
- [ ] Migration script framework ready

## Implementation Strategy

### Phase A: Architectural Restructure (Week 1-2)
**Week 1**: Directory reorganization
- Create target directory structure
- Map existing tests to new domain-based locations
- Implement migration helper script

**Week 2**: Layer separation & fixture optimization
- Establish unit/integration/e2e separation within domains
- Streamline fixture hierarchy with domain-specific extensions
- Update fixture imports and dependencies

### Phase B: DI Pattern Migration (Week 3-5)
**Week 3**: Auth domain migration (~50 files)
- Replace `AuthService(db_session)` with `create_test_auth_service(db_session)`
- Update auth-related tests to use DI fixtures
- Standardize test user creation patterns

**Week 4**: Repository & Usecase migration (~100 files)
- Update repository tests to use `*_repository_with_di` fixtures
- Update usecase tests to use `*_usecase_with_di` fixtures
- Ensure proper mocking patterns

**Week 5**: Integration tests & user standardization (~150 files)
- Migrate integration tests to DI pattern
- Replace custom user creation with `test_user`, `test_user_with_wallet` fixtures
- Update endpoint tests

### Phase C: Performance & Quality (Week 6)
- Performance optimization through better test organization
- Coverage validation (maintain ≥47% baseline)
- Documentation updates and cleanup

## Target Architecture

```
backend/tests/
├── domains/
│   ├── auth/
│   │   ├── unit/           # AuthService, JWT, password validation
│   │   ├── integration/    # Auth endpoints, OAuth flows
│   │   └── e2e/           # Complete auth workflows
│   ├── wallets/
│   │   ├── unit/           # WalletUsecase, repository logic
│   │   ├── integration/    # Wallet API endpoints
│   │   └── e2e/           # Wallet workflows
│   ├── admin/ & defi/     # Similar structure
├── infrastructure/
│   ├── database/          # Migration tests, connections
│   ├── security/          # Security middleware, rate limiting
│   ├── monitoring/        # Metrics, logging
│   └── external_apis/     # Third-party integrations
├── shared/
│   ├── fixtures/          # Core fixtures (≤20 items)
│   │   ├── core.py       # Database, FastAPI app
│   │   ├── users.py      # Standard user fixtures
│   │   └── domain_fixtures/ # Domain-specific extensions
│   ├── strategies/        # Hypothesis strategies
│   └── utils/            # Test utilities
└── performance/           # Load tests, benchmarks
```

## Creative Phases Required
- [ ] **Fixture Architecture Design**: Optimize domain-specific fixture hierarchies
- [ ] **Migration Strategy Design**: Create safe, incremental migration approach
- [ ] **Directory Structure Design**: Finalize domain boundaries and organization

## Dependencies
- Completion of Phase 6 DI refactoring (in progress)
- Existing DI test patterns (`test_*_di.py` files)
- Current fixture organization in 12 files

## Challenges & Mitigations

**Challenge 1**: Large-scale file moves creating merge conflicts
- **Mitigation**: Execute Phase A in short-lived branches, coordinate with team, domain-by-domain migration

**Challenge 2**: Breaking existing tests during migration
- **Mitigation**: Validate tests after each domain move, maintain backward compatibility during transition

**Challenge 3**: DI fixture pattern inconsistency
- **Mitigation**: Follow established patterns in existing `test_*_di.py` examples, create pattern documentation

**Challenge 4**: Test discovery performance degradation
- **Mitigation**: Monitor test collection times, optimize fixture loading, leverage pytest's intelligent collection

**Challenge 5**: Coverage regression during restructure
- **Mitigation**: Coverage gate enforcement, before/after validation per domain

## Detailed Migration Checklist

### Phase A Checklist
- [ ] Create new directory structure in `backend/tests/`
- [ ] Develop migration script for file moves
- [ ] Map existing tests to domain categories
- [ ] Execute domain-by-domain file moves
- [ ] Update imports and path references
- [ ] Establish unit/integration/e2e separation
- [ ] Optimize fixture hierarchy

### Phase B Checklist
**Auth Domain**:
- [ ] Replace direct service instantiation with DI fixtures
- [ ] Update `test_auth_*.py` files
- [ ] Standardize user creation patterns
- [ ] Validate all auth tests pass

**Repository Layer**:
- [ ] Update all repository tests to use `*_repository_with_di`
- [ ] Ensure proper mock setup patterns
- [ ] Validate repository test isolation

**Usecase Layer**:
- [ ] Update all usecase tests to use `*_usecase_with_di`
- [ ] Implement proper usecase dependency mocking
- [ ] Validate business logic test coverage

**Integration Layer**:
- [ ] Update endpoint tests to use DI pattern
- [ ] Standardize test user fixtures across integration tests
- [ ] Validate API integration test coverage

### Phase C Checklist
- [ ] Run comprehensive test suite validation
- [ ] Monitor and optimize test performance
- [ ] Validate coverage baseline maintained
- [ ] Update test documentation and guidelines
- [ ] Clean up legacy patterns and deprecated code

## Success Metrics
- 100% of tests organized under `domains/` and `infrastructure/`
- Every domain has `unit/`, `integration/`, (optional) `e2e/` structure
- 0 legacy DI patterns remaining (`AuthService(db_session)` eliminated)
- All tests use standardized fixtures (`test_user`, `test_user_with_wallet`)
- Test coverage ≥47% maintained
- Improved test discovery and execution performance

## Risk Register
| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| Merge conflicts from file moves | Medium | High | Phased migration, team coordination |
| Test breakage during migration | Medium | High | Domain-by-domain validation |
| Performance regression | Low | Medium | Monitor collection times, optimize fixtures |
| Coverage drop | Low | Medium | Coverage gates, domain-level validation |

## Next Steps
1. **CREATIVE MODE**: Design optimized fixture architecture and migration strategy
2. **IMPLEMENT MODE**: Execute phased migration with validation at each step 