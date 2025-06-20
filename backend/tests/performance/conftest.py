from pathlib import Path

import pytest

_PERF_DIR = Path(__file__).parent.resolve()


def pytest_collection_modifyitems(config, items):
    """Automatically mark all tests in the performance suite with the 'performance' marker.

    This allows us to exclude them by default via ``-m 'not performance'`` and include
    them explicitly when needed (e.g., in CI or local benchmarking).
    """
    for item in items:
        try:
            # ``item.fspath`` is a py.path object; convert to pathlib for ease.
            test_path = Path(str(item.fspath)).resolve()
        except Exception:
            # In rare cases ``fspath`` may not be available; skip marking.
            continue

        if _PERF_DIR in test_path.parents:
            item.add_marker(pytest.mark.performance)
