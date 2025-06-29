# Fixture Best Practices

This document summarizes best practices and common anti-patterns for using fixtures effectively in tests.

## Best Practices

- **Compose Fixtures Thoughtfully**: Combine only the fixtures you need for a test to minimize setup overhead.
- **Use Proper Scoping**: Leverage session, module, and function scopes to balance performance and isolation.
- **Prefer Transactions**: Use transactional rollbacks for database fixtures (`clean_db_session`) to ensure isolation without recreating the database.
- **Mock External Services**: Always mock external dependencies (`mock_external_apis`, `mock_web3`) to avoid network calls and flakiness.
- **Parameterize Tests**: Use `pytest.mark.parametrize` to test multiple scenarios with minimal duplication.
- **Document Template Usage**: Reference `backend/tests/examples/templates` for reusable patterns.
- **Isolate Side Effects**: Clean up environment changes (files, environment variables) within fixtures.
- **Use Factory Fixtures**: Create factory functions for complex data setup (`create_user_and_wallet`).
- **Keep Tests Deterministic**: Ensure tests do not depend on external state or timing.

## Anti-Patterns

- **Over-Loading Fixtures**: Avoid adding all fixtures to every test; include only necessary ones.
- **Module-Scoped Mutable State**: Do not store mutable state in module-scoped fixtures; prefer function scope.
- **Network Calls in Tests**: Never make real network or database calls in tests; always mock.
- **Implicit Dependencies**: Do not rely on fixtures imported in `conftest.py` without explicit use in the test signature.
- **Hard-Coded Test Data**: Avoid embedding large hard-coded data; use `test_data` fixtures for consistency.
- **Uncontrolled Cleanup**: Failing to clean up temporary files or environment variables can lead to test bleed-through.
- **Ignoring Performance**: Running expensive setup for every test can slow down the suite; use session/module scopes appropriately.

## Resources

- [Pytest Fixture Documentation](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [Pytest-Asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
