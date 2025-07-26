import os
import pytest

from app.utils.rate_limiter import login_rate_limiter


@pytest.fixture(autouse=True)
async def _cleanup_auth_state(test_di_container_with_db):
    """Reset authentication-related global state between tests.

    This fixture ensures a clean environment for each test by:
    1. Resetting JWT-related environment variables.
    2. Clearing the login rate-limiter.
    3. Clearing any cached JWT state.
    4. Re-registering a fresh ``jwt_utils`` instance in the DI container.
    """
    # ------------------------------------------------------------------
    # 1. Environment variable hygiene
    # ------------------------------------------------------------------
    test_env_vars = [
        "JWT_SECRET_KEY",
        "JWT_KEYS",
        "ACTIVE_JWT_KID",
        "JWT_ALGORITHM",
    ]
    for var in test_env_vars:
        os.environ.pop(var, None)

    # Provide deterministic secret/algorithm so tokens can be decoded in tests
    os.environ["JWT_SECRET_KEY"] = "clean-test-key-per-test"
    os.environ["JWT_ALGORITHM"] = "HS256"

    # ------------------------------------------------------------------
    # 2. Clear rate-limiter & JWT global state
    # ------------------------------------------------------------------
    login_rate_limiter.clear()

    from app.utils.jwt import clear_jwt_state

    clear_jwt_state()

    # ------------------------------------------------------------------
    # 3. Re-instantiate JWT utils in DI container so tests pick up fresh config
    # ------------------------------------------------------------------
    from app.core.config import Configuration
    from app.utils.jwt import JWTUtils

    fresh_config = Configuration()
    audit = test_di_container_with_db.get_core("audit")
    fresh_jwt_utils = JWTUtils(fresh_config, audit)

    test_di_container_with_db.register_utility("jwt_utils", fresh_jwt_utils)

    yield

    # ------------------------------------------------------------------
    # 4. Cleanup – remove variables set for this test
    # ------------------------------------------------------------------
    for var in test_env_vars:
        os.environ.pop(var, None) 