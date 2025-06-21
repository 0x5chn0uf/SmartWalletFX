# End-to-End Test Suite

This directory contains comprehensive end-to-end tests for the database backup and restore functionality. These tests validate the complete backup/restore workflow in real-world scenarios using ephemeral PostgreSQL containers.

## Overview

The E2E test suite includes:

- **Basic backup/restore cycle tests** - Validate core functionality
- **Performance tests** - Ensure performance requirements are met
- **Failure scenario tests** - Test error handling and edge cases
- **CLI integration tests** - Test command-line interface
- **Data integrity validation** - Ensure data is preserved correctly

## Prerequisites

### Local Development

1. **Docker**: Required for running ephemeral PostgreSQL containers
2. **Python dependencies**: Install test dependencies
   ```bash
   cd backend
   pip install -e .[dev]
   pip install docker psutil
   ```

3. **Docker Compose E2E services**: Start the test services
   ```bash
   docker compose -f docker-compose.e2e.yml up -d
   ```

### CI/CD

The E2E tests run automatically in the CI pipeline with the following services:
- PostgreSQL 15 (port 5434) for basic tests
- PostgreSQL 15 (port 5435) for large dataset tests
- Redis (port 6381) for caching tests

## Running Tests

### All E2E Tests

```bash
cd backend
pytest -m e2e -v
```

### Performance Tests Only

```bash
cd backend
pytest -m performance -v
```

### Specific Test Categories

```bash
# Basic backup/restore functionality
pytest tests/e2e/test_backup_restore_e2e.py::TestBackupRestoreE2E -v

# Failure scenarios
pytest tests/e2e/test_backup_restore_e2e.py::TestBackupRestoreFailureScenarios -v

# Performance benchmarks
pytest tests/e2e/test_performance.py -v
```

### With Coverage

```bash
cd backend
pytest -m e2e --cov=app --cov-report=html
```

## Test Structure

### TestBackupRestoreE2E

Basic end-to-end tests that validate:

- **Basic backup/restore cycle**: Complete workflow with small dataset
- **Large dataset backup/restore**: Performance testing with substantial data
- **CLI integration**: Command-line interface testing
- **Data integrity validation**: Ensure data is preserved correctly

### TestBackupRestoreFailureScenarios

Failure scenario tests that validate error handling:

- **Corrupted database**: Backup behavior with inconsistent database state
- **Corrupted backup files**: Restore behavior with damaged backup files
- **Insufficient disk space**: Backup behavior when storage is limited
- **Invalid database URLs**: Connection failure handling
- **Concurrent modifications**: Backup behavior during database changes
- **Existing data conflicts**: Restore behavior with pre-existing data
- **Version compatibility**: Cross-PostgreSQL version restore testing

### TestBackupPerformance

Performance benchmarks that validate:

- **1GB backup requirement**: Ensure backup completes within 30s for 1GB dataset
- **Memory usage monitoring**: Track memory consumption during operations
- **CPU usage monitoring**: Monitor CPU utilization
- **Concurrent operations**: Test multiple simultaneous backups
- **Compression performance**: Validate compression overhead

### TestRestorePerformance

Restore performance benchmarks:

- **1GB restore requirement**: Ensure restore completes within 60s for 1GB dataset
- **Memory usage during restore**: Monitor memory consumption
- **Data integrity after restore**: Validate restored data correctness

### TestSystemPerformance

System-wide performance tests:

- **Complete backup-restore cycle**: End-to-end performance validation
- **Resource cleanup**: Ensure proper cleanup after operations

## Test Data Management

The test suite uses the `TestDataManager` utility class (`backend/tests/utils/test_data_manager.py`) to:

- Generate realistic database schemas
- Populate test data (small and large volumes)
- Validate data integrity between databases
- Measure database sizes

### Data Volumes

- **Small dataset**: ~1MB, suitable for basic functionality testing
- **Large dataset**: ~1GB, suitable for performance testing

The large dataset includes:
- 10,000 users
- 30,000 wallets
- 500,000 transactions
- 150,000 token balances
- 50,000 portfolio snapshots
- 200,000 audit logs

## Performance Requirements

The test suite validates the following performance requirements from Task 8:

- **Backup**: < 30 seconds for 1GB dataset
- **Restore**: < 60 seconds for 1GB dataset
- **Memory usage**: < 500MB increase during backup, < 1GB during restore
- **CPU usage**: < 80% average during operations
- **Resource cleanup**: < 10% memory increase after operations

## Test Environment

### Docker Services

The E2E tests use the following Docker services (defined in `docker-compose.e2e.yml`):

- **postgres-e2e** (port 5434): Standard test database
- **postgres-large** (port 5435): Large dataset database
- **postgres-16** (port 5436): PostgreSQL 16 for version compatibility testing
- **redis-e2e** (port 6381): Redis for caching tests
- **postgres-restore** (port 5437): Target database for restore tests

### Container Management

Tests automatically:
- Start fresh PostgreSQL containers for isolation
- Wait for containers to be ready
- Load appropriate test data
- Clean up containers after tests

## Interpreting Results

### Test Output

Successful tests will show:
```
✓ test_basic_backup_restore_cycle
✓ test_large_dataset_backup_restore
✓ test_backup_performance_1gb_requirement
```

### Performance Metrics

Performance tests output detailed metrics:
```
Backup Performance Metrics:
  Time: 25.34s
  Size: 856.72 MB
  Rate: 33.78 MB/s

Memory Usage Metrics:
  Initial: 45.23 MB
  Peak: 234.56 MB
  Increase: 189.33 MB
  Duration: 25.34s
```

### Failure Analysis

Failed tests will show:
- Detailed error messages
- Expected vs actual behavior
- Performance metrics (if applicable)
- Resource usage information

## Troubleshooting

### Common Issues

1. **Docker containers not starting**
   ```bash
   # Check Docker service
   docker ps
   
   # Restart Docker Compose services
   docker compose -f docker-compose.e2e.yml down -v
   docker compose -f docker-compose.e2e.yml up -d
   ```

2. **Port conflicts**
   ```bash
   # Check for processes using test ports
   lsof -i :5434
   lsof -i :5435
   
   # Kill conflicting processes
   sudo kill -9 <PID>
   ```

3. **Insufficient disk space**
   ```bash
   # Clean up Docker resources
   docker system prune -a
   docker volume prune
   ```

4. **Memory issues**
   ```bash
   # Increase Docker memory limit
   # In Docker Desktop: Settings > Resources > Memory
   ```

### Debug Mode

Run tests with verbose output for debugging:
```bash
pytest -m e2e -v -s --tb=long
```

### Isolated Testing

Run a single test for debugging:
```bash
pytest tests/e2e/test_backup_restore_e2e.py::TestBackupRestoreE2E::test_basic_backup_restore_cycle -v -s
```

## CI/CD Integration

The E2E tests are integrated into the CI pipeline:

- **Triggered on**: Backend changes
- **Dependencies**: Unit tests, integration tests
- **Services**: PostgreSQL containers, Redis
- **Artifacts**: Test results, performance metrics
- **Failure handling**: Detailed error reporting

### CI Job Configuration

The E2E test job:
- Runs on Ubuntu latest
- Uses Python 3.12
- Starts required Docker services
- Loads test data
- Runs E2E and performance tests
- Uploads test artifacts

## Contributing

When adding new E2E tests:

1. **Follow naming conventions**: Use descriptive test names
2. **Add appropriate markers**: Use `@pytest.mark.e2e` or `@pytest.mark.performance`
3. **Include documentation**: Add docstrings explaining test purpose
4. **Handle cleanup**: Ensure containers are properly cleaned up
5. **Add to CI**: Update CI configuration if needed

### Test Guidelines

- **Isolation**: Each test should be independent
- **Cleanup**: Always clean up resources
- **Performance**: Monitor resource usage
- **Error handling**: Test both success and failure scenarios
- **Documentation**: Explain complex test logic

## Related Files

- `docker-compose.e2e.yml`: Docker services configuration
- `backend/tests/utils/test_data_manager.py`: Test data management utilities
- `backend/tests/fixtures/large_dataset.sql`: Large dataset SQL fixture
- `backend/tests/fixtures/init.sql`: Basic dataset SQL fixture
- `.github/workflows/ci-cd.yml`: CI pipeline configuration 