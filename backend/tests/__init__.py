pytest_plugins = [
    "tests.plugins.audit_validator",
]

import unittest.mock as _umock  # noqa: E402

# ---------------------------------------------------------------------------
# Compatibility shim: some legacy tests import `pytest.mock.patch` instead of
# using the dedicated `mocker` fixture from *pytest-mock*.  Provide a minimal
# fallback so expressions like `pytest.mock.patch(...)` resolve to
# `unittest.mock.patch` and do not raise AttributeError when the plugin is not
# installed.
# ---------------------------------------------------------------------------
import pytest as _pytest  # noqa: E402 – local import after pytest_plugins declaration

if not hasattr(_pytest, "mock"):
    # Expose the *unittest.mock* module under pytest.mock
    setattr(_pytest, "mock", _umock)
