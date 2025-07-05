"""Pytest plugin that sets up infrastructure for property-test templates.

Responsibilities:
1. Register a custom "property" marker so tests can be filtered via
   ``pytest -m property`` or in the CI job.
2. Ensure Hypothesis runs with deterministic settings (seeded) when the
   ``CI`` environment variable is present.
"""
from __future__ import annotations


import os

import pytest
from hypothesis import HealthCheck, settings


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover
    # Register marker description for --markers output
    config.addinivalue_line(
        "markers", "property: mark a test as a property-based check"
    )

    # If running in CI, activate the deterministic profile (defined in templates)
    if os.getenv("CI"):
        settings.register_profile(
            "ci",
            max_examples=200,
            deadline=None,
            suppress_health_check=[HealthCheck.too_slow],
        )
        settings.load_profile("ci")


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
):  # noqa: D401
    """Automatically add the `property` mark to any test collected from the *templates* package.

    This spares developers from having to repeat ``pytestmark = pytest.mark.property`` in every
    template module and guarantees they are executed when filtering with ``-m property``.
    """

    for item in items:
        if "tests/templates/" in item.nodeid.replace("\\", "/"):
            item.add_marker(pytest.mark.property)
